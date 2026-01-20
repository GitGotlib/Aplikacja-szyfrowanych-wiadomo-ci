from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, LargeBinary, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    password_updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    totp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    totp_secret_enc: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    totp_secret_nonce: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    totp_secret_tag: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)

    hmac_key_enc: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    hmac_key_nonce: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    hmac_key_tag: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    session_token_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False, unique=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    user: Mapped[User] = relationship(back_populates="sessions")

    __table_args__ = (
        Index("ux_user_sessions_token_hash", "session_token_hash", unique=True),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    sender_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)

    content_key_enc: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    content_key_nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    content_key_tag: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    subject_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    subject_nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    subject_tag: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    body_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    body_nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    body_tag: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    hmac_sha256: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    deleted_by_sender_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    recipients: Mapped[list["MessageRecipient"]] = relationship(back_populates="message", cascade="all, delete-orphan")
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="message", cascade="all, delete-orphan")


class MessageRecipient(Base):
    __tablename__ = "message_recipients"

    message_id: Mapped[str] = mapped_column(String, ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True)
    recipient_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True, index=True)

    delivered_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    read_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    authenticity_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    message: Mapped[Message] = relationship(back_populates="recipients")


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    message_id: Mapped[str] = mapped_column(String, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)

    filename: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    blob_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    blob_nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    blob_tag: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    message: Mapped[Message] = relationship(back_populates="attachments")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    event_type: Mapped[str] = mapped_column(String, nullable=False)
    event_time: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)

    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    details_redacted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# Helpful indexes beyond schema.sql (kept minimal)
Index("idx_attachments_message", Attachment.message_id)
Index("idx_messages_sender", Message.sender_user_id)
Index("idx_message_recipients_recipient", MessageRecipient.recipient_user_id)
