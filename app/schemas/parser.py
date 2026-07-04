from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProxySchema(BaseModel):
    type: str = "socks5"
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    secret: Optional[str] = None


class ParseChannelRequest(BaseModel):
    phone: str = Field(..., example="+79001234567")
    channel: str = Field(..., example="durov", description="Username канала без @")
    limit: int = Field(default=100, ge=1, le=1000, description="Количество последних постов")
    proxy: Optional[ProxySchema] = None


class MessageReactionSchema(BaseModel):
    emoji: str
    count: int

    model_config = {"from_attributes": True}


class MessageSchema(BaseModel):
    id: int
    channel_id: int
    message_id: int
    text: Optional[str]
    date: datetime
    views: Optional[int]
    forwards: Optional[int]
    replies: Optional[int]
    has_media: bool
    media_type: Optional[str]
    link: Optional[str]
    reactions: list[MessageReactionSchema] = []

    model_config = {"from_attributes": True}


class ChannelSchema(BaseModel):
    id: int
    username: Optional[str]
    title: str
    about: Optional[str]
    participants_count: Optional[int]
    is_verified: bool
    scraped_at: datetime
    messages_count: Optional[int] = None

    model_config = {"from_attributes": True}


class ParseJobSchema(BaseModel):
    id: int
    channel_id: Optional[int]
    channel_username: str
    phone: str
    status: str
    messages_limit: int
    messages_parsed: int
    messages_new: int
    messages_updated: int
    error_message: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ChannelStatsSchema(BaseModel):
    channel_id: int
    title: str
    username: Optional[str]
    participants_count: Optional[int]
    total_messages: int
    total_views: Optional[int] = None
    avg_views: Optional[float] = None
    total_forwards: Optional[int] = None
    avg_forwards: Optional[float] = None
    messages_with_media: Optional[int] = None
    media_breakdown: Optional[dict[str, int]] = None
    top_posts_by_views: Optional[list[dict]] = None
