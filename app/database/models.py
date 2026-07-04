from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(512))
    about: Mapped[str | None] = mapped_column(Text, nullable=True)
    participants_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_broadcast: Mapped[bool] = mapped_column(Boolean, default=True)
    linked_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    messages: Mapped[list["Message"]] = relationship(back_populates="channel")
    parse_jobs: Mapped[list["ParseJob"]] = relationship(back_populates="channel")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("channel_id", "message_id", name="uq_channel_message"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("channels.id"), index=True)
    message_id: Mapped[int] = mapped_column(Integer, index=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    edit_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    forwards: Mapped[int | None] = mapped_column(Integer, nullable=True)
    replies: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_media: Mapped[bool] = mapped_column(Boolean, default=False)
    media_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    media_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    grouped_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    post_author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    channel: Mapped["Channel"] = relationship(back_populates="messages")
    reactions: Mapped[list["MessageReaction"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )


class MessageReaction(Base):
    __tablename__ = "message_reactions"
    __table_args__ = (
        UniqueConstraint("message_id", "emoji", name="uq_message_reaction"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("messages.id"), index=True)
    emoji: Mapped[str] = mapped_column(String(64))
    count: Mapped[int] = mapped_column(Integer, default=0)

    message: Mapped["Message"] = relationship(back_populates="reactions")


class ParseJob(Base):
    __tablename__ = "parse_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("channels.id"), nullable=True, index=True
    )
    channel_username: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    messages_limit: Mapped[int] = mapped_column(Integer, default=100)
    messages_parsed: Mapped[int] = mapped_column(Integer, default=0)
    messages_new: Mapped[int] = mapped_column(Integer, default=0)
    messages_updated: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    channel: Mapped["Channel | None"] = relationship(back_populates="parse_jobs")
