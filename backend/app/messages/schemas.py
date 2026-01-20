from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SendMessageResponse(BaseModel):
    id: str


class InboxMessageItem(BaseModel):
    id: str
    sender_username: str
    created_at: datetime
    read: bool
    has_attachments: bool
    authenticity_verified: bool


class SentMessageItem(BaseModel):
    id: str
    created_at: datetime
    recipients_count: int
    has_attachments: bool


class AttachmentMeta(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int


class MessageDetail(BaseModel):
    id: str
    sender_username: str
    created_at: datetime
    subject: str
    body: str
    attachments: list[AttachmentMeta]
    authenticity_verified: bool


class DeleteResponse(BaseModel):
    ok: bool = True


class MarkReadResponse(BaseModel):
    ok: bool = True
