from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.models import User
from app.db.session import get_db
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


@router.post("/send", response_model=SendMessageResponse)
def send(
    recipients: str = Form(...),
    subject: str = Form(..., max_length=200),
    body: str = Form(..., max_length=20000),
    files: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SendMessageResponse:
    # Read all attachments in-memory (POC); enforce server-side size limits.
    file_tuples: list[tuple[str, str, bytes]] = []
    for f in files:
        data = f.file.read()
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
    filename, content_type, data = download_attachment(db, current_user, message_id, attachment_id)
    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    return Response(content=data, media_type=content_type, headers=headers)
