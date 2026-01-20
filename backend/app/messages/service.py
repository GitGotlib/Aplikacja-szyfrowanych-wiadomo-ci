from __future__ import annotations

import datetime as dt
import json
import os
import uuid

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthorizationError, IntegrityError, ValidationError
from app.crypto.aes_gcm import AesGcmCipher
from app.crypto.hmac_sha256 import constant_time_equals, hmac_sha256
from app.crypto.key_management import generate_aes256_key
from app.db.models import Attachment, Message, MessageRecipient, User, utcnow


def _aad(purpose: str, *parts: str) -> bytes:
    return (purpose + ":" + ":".join(parts)).encode("utf-8")


def _safe_filename(name: str) -> str:
    # Prevent path traversal in Content-Disposition contexts.
    name = name.replace("\\", "/")
    if "/" in name:
        name = name.split("/")[-1]
    return name[:255]


def _encode_len_prefixed(chunks: list[bytes]) -> bytes:
    out = bytearray()
    for c in chunks:
        out.extend(len(c).to_bytes(4, "big"))
        out.extend(c)
    return bytes(out)


def _message_hmac_payload(
    *,
    message: Message,
    recipient_ids_sorted: list[str],
    attachments: list[Attachment],
) -> bytes:
    parts: list[bytes] = []
    parts.append(b"v1")
    parts.append(message.id.encode("utf-8"))
    parts.append(message.sender_user_id.encode("utf-8"))
    for rid in recipient_ids_sorted:
        parts.append(rid.encode("utf-8"))

    # Include all encrypted fields
    parts.extend(
        [
            message.content_key_enc,
            message.content_key_nonce,
            message.content_key_tag,
            message.subject_ciphertext,
            message.subject_nonce,
            message.subject_tag,
            message.body_ciphertext,
            message.body_nonce,
            message.body_tag,
        ]
    )

    # Attachments are integral: include metadata + encrypted bytes.
    for a in sorted(attachments, key=lambda x: x.id):
        parts.append(a.id.encode("utf-8"))
        parts.append(a.filename.encode("utf-8"))
        parts.append(a.content_type.encode("utf-8"))
        parts.append(str(a.size_bytes).encode("utf-8"))
        parts.append(a.blob_ciphertext)
        parts.append(a.blob_nonce)
        parts.append(a.blob_tag)

    return _encode_len_prefixed(parts)


def _decrypt_user_hmac_key(user: User) -> bytes:
    if user.hmac_key_enc is None or user.hmac_key_nonce is None or user.hmac_key_tag is None:
        raise IntegrityError("missing hmac key")

    cipher = AesGcmCipher(settings.user_hmac_kek_bytes)
    return cipher.decrypt(
        user.hmac_key_enc,
        user.hmac_key_nonce,
        user.hmac_key_tag,
        aad=_aad("users:hmac_key", user.id),
    )


def send_message(
    *,
    db: Session,
    sender: User,
    recipients_json: str,
    subject: str,
    body: str,
    files: list[tuple[str, str, bytes]],
) -> Message:
    try:
        recipients_raw = json.loads(recipients_json)
    except json.JSONDecodeError as exc:
        raise ValidationError("Invalid recipients") from exc

    if not isinstance(recipients_raw, list) or not recipients_raw:
        raise ValidationError("Invalid recipients")

    if len(recipients_raw) > settings.max_recipients_per_message:
        raise ValidationError("Too many recipients")

    recipient_identifiers: list[str] = []
    for r in recipients_raw:
        if not isinstance(r, str):
            raise ValidationError("Invalid recipients")
        candidate = r.strip()
        if not candidate:
            raise ValidationError("Invalid recipients")
        recipient_identifiers.append(candidate)

    # Resolve recipients by username or email.
    recipients: list[User] = []
    for ident in recipient_identifiers:
        q = select(User).where((User.username == ident) | (User.email == ident.lower()))
        u = db.execute(q).scalar_one_or_none()
        if u is None or not u.is_active:
            raise ValidationError("Invalid recipients")
        recipients.append(u)

    # Deduplicate by user_id.
    uniq: dict[str, User] = {u.id: u for u in recipients}
    if sender.id in uniq:
        # allow self-send only if explicitly needed; keep minimal: reject.
        raise ValidationError("Invalid recipients")

    recipient_ids_sorted = sorted(uniq.keys())

    now = utcnow()
    message_id = str(uuid.uuid4())

    # Envelope encryption
    dek = generate_aes256_key()

    kek_cipher = AesGcmCipher(settings.data_key_bytes)
    dek_enc = kek_cipher.encrypt(dek, aad=_aad("messages:dek", message_id))

    dek_cipher = AesGcmCipher(dek)

    subject_enc = dek_cipher.encrypt(subject.encode("utf-8"), aad=_aad("messages:subject", message_id))
    body_enc = dek_cipher.encrypt(body.encode("utf-8"), aad=_aad("messages:body", message_id))

    message = Message(
        id=message_id,
        sender_user_id=sender.id,
        content_key_enc=dek_enc.ciphertext,
        content_key_nonce=dek_enc.nonce,
        content_key_tag=dek_enc.tag,
        subject_ciphertext=subject_enc.ciphertext,
        subject_nonce=subject_enc.nonce,
        subject_tag=subject_enc.tag,
        body_ciphertext=body_enc.ciphertext,
        body_nonce=body_enc.nonce,
        body_tag=body_enc.tag,
        hmac_sha256=b"",  # set after attachments are ready
        created_at=now,
        deleted_by_sender_at=None,
    )

    db.add(message)

    # Recipients rows
    for rid in recipient_ids_sorted:
        db.add(
            MessageRecipient(
                message_id=message_id,
                recipient_user_id=rid,
                delivered_at=now,
                read_at=None,
                deleted_at=None,
                authenticity_verified=False,
            )
        )

    # Attachments
    attachments: list[Attachment] = []
    total_bytes = 0
    for original_filename, content_type, data in files:
        total_bytes += len(data)
        if len(data) > settings.max_attachment_bytes:
            raise ValidationError("Attachment too large")
        if total_bytes > settings.max_attachment_bytes:
            raise ValidationError("Attachments too large")

        att_id = str(uuid.uuid4())
        enc = dek_cipher.encrypt(data, aad=_aad("attachments:blob", message_id, att_id))
        a = Attachment(
            id=att_id,
            message_id=message_id,
            filename=_safe_filename(original_filename or "attachment"),
            content_type=(content_type or "application/octet-stream")[:255],
            size_bytes=len(data),
            blob_ciphertext=enc.ciphertext,
            blob_nonce=enc.nonce,
            blob_tag=enc.tag,
            created_at=now,
        )
        attachments.append(a)
        db.add(a)

    # HMAC over integral message + attachments.
    sender_hmac_key = _decrypt_user_hmac_key(sender)
    payload = _message_hmac_payload(message=message, recipient_ids_sorted=recipient_ids_sorted, attachments=attachments)
    message.hmac_sha256 = hmac_sha256(sender_hmac_key, payload)

    db.commit()
    db.refresh(message)
    return message


def _decrypt_dek(message: Message) -> bytes:
    kek_cipher = AesGcmCipher(settings.data_key_bytes)
    return kek_cipher.decrypt(
        message.content_key_enc,
        message.content_key_nonce,
        message.content_key_tag,
        aad=_aad("messages:dek", message.id),
    )


def _verify_authenticity(db: Session, message: Message, sender: User) -> bool:
    recipients = db.execute(select(MessageRecipient).where(MessageRecipient.message_id == message.id)).scalars().all()
    recipient_ids_sorted = sorted([r.recipient_user_id for r in recipients])
    attachments = db.execute(select(Attachment).where(Attachment.message_id == message.id)).scalars().all()

    sender_hmac_key = _decrypt_user_hmac_key(sender)
    payload = _message_hmac_payload(message=message, recipient_ids_sorted=recipient_ids_sorted, attachments=attachments)
    expected = hmac_sha256(sender_hmac_key, payload)
    return constant_time_equals(expected, message.hmac_sha256)


def list_inbox(db: Session, user: User) -> list[tuple[MessageRecipient, Message, User, bool]]:
    q = (
        select(MessageRecipient, Message, User)
        .join(Message, Message.id == MessageRecipient.message_id)
        .join(User, User.id == Message.sender_user_id)
        .where(MessageRecipient.recipient_user_id == user.id)
        .where(MessageRecipient.deleted_at.is_(None))
        .order_by(Message.created_at.desc())
    )
    rows = db.execute(q).all()

    result: list[tuple[MessageRecipient, Message, User, bool]] = []
    for mr, m, sender in rows:
        has_attachments = db.execute(select(Attachment.id).where(Attachment.message_id == m.id).limit(1)).first() is not None
        result.append((mr, m, sender, has_attachments))
    return result


def list_sent(db: Session, user: User) -> list[tuple[Message, int, bool]]:
    q = select(Message).where(Message.sender_user_id == user.id).where(Message.deleted_by_sender_at.is_(None)).order_by(Message.created_at.desc())
    messages = db.execute(q).scalars().all()

    out: list[tuple[Message, int, bool]] = []
    for m in messages:
        rcpt_count = len(db.execute(select(MessageRecipient).where(MessageRecipient.message_id == m.id)).scalars().all())
        has_attachments = db.execute(select(Attachment.id).where(Attachment.message_id == m.id).limit(1)).first() is not None
        out.append((m, rcpt_count, has_attachments))
    return out


def get_message_for_user(db: Session, user: User, message_id: str) -> tuple[Message, User, MessageRecipient | None]:
    m = db.get(Message, message_id)
    if m is None:
        raise AuthorizationError("not found")

    sender = db.get(User, m.sender_user_id)
    if sender is None:
        raise AuthorizationError("not found")

    if m.sender_user_id == user.id:
        return m, sender, None

    mr = db.execute(
        select(MessageRecipient)
        .where(MessageRecipient.message_id == message_id)
        .where(MessageRecipient.recipient_user_id == user.id)
        .where(MessageRecipient.deleted_at.is_(None))
    ).scalar_one_or_none()

    if mr is None:
        raise AuthorizationError("not found")

    return m, sender, mr


def read_message_detail(db: Session, user: User, message_id: str) -> tuple[Message, User, list[Attachment], str, str, bool]:
    m, sender, mr = get_message_for_user(db, user, message_id)

    ok = _verify_authenticity(db, m, sender)
    if not ok:
        raise IntegrityError("bad hmac")

    attachments = db.execute(select(Attachment).where(Attachment.message_id == message_id)).scalars().all()

    dek = _decrypt_dek(m)
    dek_cipher = AesGcmCipher(dek)

    subject = dek_cipher.decrypt(m.subject_ciphertext, m.subject_nonce, m.subject_tag, aad=_aad("messages:subject", m.id)).decode("utf-8")
    body = dek_cipher.decrypt(m.body_ciphertext, m.body_nonce, m.body_tag, aad=_aad("messages:body", m.id)).decode("utf-8")

    if mr is not None and mr.read_at is None:
        mr.read_at = utcnow()
        mr.authenticity_verified = True
        db.commit()

    return m, sender, attachments, subject, body, True


def delete_message_for_user(db: Session, user: User, message_id: str) -> None:
    m = db.get(Message, message_id)
    if m is None:
        raise AuthorizationError("not found")

    if m.sender_user_id == user.id:
        m.deleted_by_sender_at = utcnow()
        db.commit()
        return

    mr = db.execute(
        select(MessageRecipient)
        .where(MessageRecipient.message_id == message_id)
        .where(MessageRecipient.recipient_user_id == user.id)
        .where(MessageRecipient.deleted_at.is_(None))
    ).scalar_one_or_none()

    if mr is None:
        raise AuthorizationError("not found")

    mr.deleted_at = utcnow()
    db.commit()


def download_attachment(db: Session, user: User, message_id: str, attachment_id: str) -> tuple[str, str, bytes]:
    m, sender, _mr = get_message_for_user(db, user, message_id)

    ok = _verify_authenticity(db, m, sender)
    if not ok:
        raise IntegrityError("bad hmac")

    a = db.execute(
        select(Attachment)
        .where(Attachment.id == attachment_id)
        .where(Attachment.message_id == message_id)
    ).scalar_one_or_none()

    if a is None:
        raise AuthorizationError("not found")

    dek = _decrypt_dek(m)
    dek_cipher = AesGcmCipher(dek)

    data = dek_cipher.decrypt(
        a.blob_ciphertext,
        a.blob_nonce,
        a.blob_tag,
        aad=_aad("attachments:blob", message_id, attachment_id),
    )
    return a.filename, a.content_type, data
