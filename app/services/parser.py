import logging
from datetime import datetime

from sqlalchemy.orm import Session
from telethon.errors import ChannelInvalidError, ChannelPrivateError, UsernameInvalidError
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import Channel as TgChannel

from app.database.models import Channel, Message, MessageReaction, ParseJob
from app.telegram.client import tg_manager
from app.utils.telegram_helpers import (
    build_message_link,
    detect_media_type,
    extract_reactions,
    extract_replies_count,
    normalize_channel_username,
)

logger = logging.getLogger(__name__)


class ChannelParserService:
    async def parse_channel(
        self,
        db: Session,
        phone: str,
        channel_username: str,
        limit: int = 100,
        proxy_config: dict | None = None,
    ) -> ParseJob:
        username = normalize_channel_username(channel_username)

        job = ParseJob(
            channel_username=username,
            phone=phone,
            messages_limit=limit,
            status="running",
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        try:
            client = await tg_manager.get_client(phone, proxy_config=proxy_config)
            if not client.is_connected():
                await client.connect()

            if not await client.is_user_authorized():
                raise ValueError(
                    f"Аккаунт {phone} не авторизован. Сначала вызовите POST /telegram/connect"
                )

            entity = await client.get_entity(username)
            if not isinstance(entity, TgChannel):
                raise ValueError(f"@{username} не является каналом")

            full = await client(GetFullChannelRequest(entity))
            channel = self._upsert_channel(db, entity, full.full_chat.about)

            job.channel_id = channel.id
            db.commit()

            new_count = 0
            updated_count = 0
            parsed_count = 0

            async for message in client.iter_messages(entity, limit=limit):
                if not message or message.id is None:
                    continue

                parsed_count += 1
                is_new, is_updated = self._upsert_message(db, channel, message, username)
                if is_new:
                    new_count += 1
                elif is_updated:
                    updated_count += 1

            job.status = "completed"
            job.messages_parsed = parsed_count
            job.messages_new = new_count
            job.messages_updated = updated_count
            job.finished_at = datetime.utcnow()
            db.commit()
            db.refresh(job)

            logger.info(
                "Парсинг @%s завершён: %s сообщений (%s новых, %s обновлено)",
                username,
                parsed_count,
                new_count,
                updated_count,
            )
            return job

        except (ChannelPrivateError, ChannelInvalidError, UsernameInvalidError) as exc:
            db.rollback()
            job = db.get(ParseJob, job.id)
            job.status = "failed"
            job.error_message = f"Канал недоступен: {exc}"
            job.finished_at = datetime.utcnow()
            db.commit()
            raise ValueError(job.error_message) from exc

        except Exception as exc:
            db.rollback()
            job = db.get(ParseJob, job.id)
            job.status = "failed"
            job.error_message = str(exc)
            job.finished_at = datetime.utcnow()
            db.commit()
            raise

    def _upsert_channel(self, db: Session, entity: TgChannel, about: str | None) -> Channel:
        channel = db.get(Channel, entity.id)
        now = datetime.utcnow()

        if channel is None:
            channel = Channel(
                id=entity.id,
                username=getattr(entity, "username", None),
                title=entity.title or "",
                about=about,
                participants_count=getattr(entity, "participants_count", None),
                is_verified=bool(getattr(entity, "verified", False)),
                is_broadcast=bool(getattr(entity, "broadcast", True)),
                linked_chat_id=getattr(entity, "linked_chat_id", None),
                scraped_at=now,
                updated_at=now,
            )
            db.add(channel)
        else:
            channel.username = getattr(entity, "username", None) or channel.username
            channel.title = entity.title or channel.title
            channel.about = about
            channel.participants_count = getattr(entity, "participants_count", None)
            channel.is_verified = bool(getattr(entity, "verified", False))
            channel.updated_at = now

        db.commit()
        db.refresh(channel)
        return channel

    def _upsert_message(
        self,
        db: Session,
        channel: Channel,
        tg_message,
        channel_username: str,
    ) -> tuple[bool, bool]:
        existing = (
            db.query(Message)
            .filter(
                Message.channel_id == channel.id,
                Message.message_id == tg_message.id,
            )
            .first()
        )

        has_media, media_type, media_size = detect_media_type(tg_message)
        link = build_message_link(channel_username, channel.id, tg_message.id)
        reactions = extract_reactions(tg_message)

        if existing is None:
            message = Message(
                channel_id=channel.id,
                message_id=tg_message.id,
                text=tg_message.message or tg_message.raw_text,
                date=tg_message.date.replace(tzinfo=None) if tg_message.date else datetime.utcnow(),
                edit_date=(
                    tg_message.edit_date.replace(tzinfo=None) if tg_message.edit_date else None
                ),
                views=tg_message.views,
                forwards=tg_message.forwards,
                replies=extract_replies_count(tg_message),
                has_media=has_media,
                media_type=media_type,
                media_size=media_size,
                grouped_id=tg_message.grouped_id,
                post_author=tg_message.post_author,
                is_pinned=bool(tg_message.pinned),
                link=link,
            )
            db.add(message)
            db.flush()
            self._sync_reactions(db, message, reactions)
            db.commit()
            return True, False

        changed = False
        fields = {
            "text": tg_message.message or tg_message.raw_text,
            "edit_date": (
                tg_message.edit_date.replace(tzinfo=None) if tg_message.edit_date else None
            ),
            "views": tg_message.views,
            "forwards": tg_message.forwards,
            "replies": extract_replies_count(tg_message),
            "has_media": has_media,
            "media_type": media_type,
            "media_size": media_size,
            "is_pinned": bool(tg_message.pinned),
            "link": link,
        }

        for field, value in fields.items():
            if getattr(existing, field) != value:
                setattr(existing, field, value)
                changed = True

        if changed:
            existing.scraped_at = datetime.utcnow()
            self._sync_reactions(db, existing, reactions)
            db.commit()
            return False, True

        return False, False

    def _sync_reactions(
        self,
        db: Session,
        message: Message,
        reactions: list[tuple[str, int]],
    ) -> None:
        db.query(MessageReaction).filter(MessageReaction.message_id == message.id).delete()

        for emoji, count in reactions:
            db.add(
                MessageReaction(
                    message_id=message.id,
                    emoji=emoji,
                    count=count,
                )
            )

    def get_channel_stats(self, db: Session, channel_id: int) -> dict:
        channel = db.get(Channel, channel_id)
        if not channel:
            raise ValueError("Канал не найден в базе данных")

        messages = db.query(Message).filter(Message.channel_id == channel_id).all()
        if not messages:
            return {
                "channel_id": channel_id,
                "title": channel.title,
                "username": channel.username,
                "participants_count": channel.participants_count,
                "total_messages": 0,
            }

        total_views = sum(m.views or 0 for m in messages)
        total_forwards = sum(m.forwards or 0 for m in messages)
        with_media = sum(1 for m in messages if m.has_media)

        media_breakdown: dict[str, int] = {}
        for msg in messages:
            if msg.media_type:
                media_breakdown[msg.media_type] = media_breakdown.get(msg.media_type, 0) + 1

        top_by_views = sorted(messages, key=lambda m: m.views or 0, reverse=True)[:5]

        return {
            "channel_id": channel_id,
            "title": channel.title,
            "username": channel.username,
            "participants_count": channel.participants_count,
            "total_messages": len(messages),
            "total_views": total_views,
            "avg_views": round(total_views / len(messages), 1),
            "total_forwards": total_forwards,
            "avg_forwards": round(total_forwards / len(messages), 1),
            "messages_with_media": with_media,
            "media_breakdown": media_breakdown,
            "top_posts_by_views": [
                {
                    "message_id": m.message_id,
                    "views": m.views,
                    "forwards": m.forwards,
                    "link": m.link,
                    "preview": (m.text or "")[:120],
                }
                for m in top_by_views
            ],
        }


parser_service = ChannelParserService()
