from __future__ import annotations

import re
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.exceptions import ValidationError
from app.db.models import User
from app.db.session import get_db
from app.middlewares.rate_limit import FixedWindowRateLimiter
from app.messages.schemas import (
    AttachmentMeta,
    DeleteResponse,
    InboxMessageItem,
    MarkReadResponse,
    MessageDetail,
    SendMessageResponse,
    SentMessageItem,
)
from app.messages.service import (
    delete_message_for_user,
    download_attachment,
    list_inbox,
    list_sent,
    read_message_detail,
    send_message,
)


router = APIRouter(prefix="/messages", tags=["messages"])

_send_limiter = FixedWindowRateLimiter(window_seconds=60, max_requests=settings.send_rate_limit_per_minute)


def _client_ip(request: Request) -> str:
    return request.headers.get("X-Real-IP") or (request.client.host if request.client else "unknown")


async def _read_upload_limited(f: UploadFile, *, max_bytes: int) -> bytes:
    # Stream into memory with a hard cap to prevent large payload DoS.
    buf = bytearray()
    while True:
        chunk = await f.read(1024 * 1024)  # 1 MiB
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > max_bytes:
            raise ValidationError("Attachment too large")
    return bytes(buf)


_SAFE_FALLBACK_RE = re.compile(r"[^A-Za-z0-9._\-]+")


def _content_disposition_attachment(filename: str) -> str:
    # RFC 6266 / RFC 5987
    raw = (filename or "attachment").replace("\r", "").replace("\n", "")
    fallback = _SAFE_FALLBACK_RE.sub("_", raw).strip("._") or "attachment"
    fallback = fallback[:150]
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quote(raw[:255])}"


@router.post("/send", response_model=SendMessageResponse)
async def send(
    request: Request,
    recipients: str = Form(...),
    subject: str = Form(..., max_length=200),
    body: str = Form(..., max_length=20000),
    files: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SendMessageResponse:
    _send_limiter.check(f"send:{_client_ip(request)}")

    if len(files) > settings.max_attachments_per_message:
        raise ValidationError("Too many attachments")

    # Read attachments (POC uses in-memory) but enforce strict caps during read.
    file_tuples: list[tuple[str, str, bytes]] = []
    total = 0
    for f in files:
        data = await _read_upload_limited(f, max_bytes=settings.max_attachment_bytes)
        total += len(data)
        if total > settings.max_attachment_bytes:
            raise ValidationError("Attachments too large")
        file_tuples.append((f.filename or "attachment", f.content_type or "application/octet-stream", data))

    m = send_message(db=db, sender=current_user, recipients_json=recipients, subject=subject, body=body, files=file_tuples)
    return SendMessageResponse(id=m.id)


@router.get("/inbox", response_model=list[InboxMessageItem])
def inbox(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[InboxMessageItem]:
    rows = list_inbox(db, current_user)
    out: list[InboxMessageItem] = []
    for mr, m, sender, has_att in rows:
        out.append(
            InboxMessageItem(
                id=m.id,
                sender_username=sender.username,
                created_at=m.created_at,
                read=mr.read_at is not None,
                has_attachments=has_att,
                authenticity_verified=bool(mr.authenticity_verified),
            )
        )
    return out


@router.get("/sent", response_model=list[SentMessageItem])
def sent(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[SentMessageItem]:
    rows = list_sent(db, current_user)
    out: list[SentMessageItem] = []
    for m, rcpt_count, has_att in rows:
        out.append(SentMessageItem(id=m.id, created_at=m.created_at, recipients_count=rcpt_count, has_attachments=has_att))
    return out


@router.get("/{message_id}", response_model=MessageDetail)
def detail(message_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> MessageDetail:
    m, sender, attachments, subject, body, ok = read_message_detail(db, current_user, message_id)
    metas = [
        AttachmentMeta(id=a.id, filename=a.filename, content_type=a.content_type, size_bytes=a.size_bytes)
        for a in attachments
    ]
    return MessageDetail(
        id=m.id,
        sender_username=sender.username,
        created_at=m.created_at,
        subject=subject,
        body=body,
        attachments=metas,
        authenticity_verified=ok,
    )


@router.delete("/{message_id}", response_model=DeleteResponse)
def delete(message_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> DeleteResponse:
    delete_message_for_user(db, current_user, message_id)
    return DeleteResponse(ok=True)


@router.get("/{message_id}/attachments/{attachment_id}")
def get_attachment(
    message_id: str,
    attachment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filename, _content_type, data = download_attachment(db, current_user, message_id, attachment_id)
    headers = {"Content-Disposition": _content_disposition_attachment(filename)}
    # Force download and avoid reflecting attacker-controlled types.
    return Response(content=data, media_type="application/octet-stream", headers=headers)
