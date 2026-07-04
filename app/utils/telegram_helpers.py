from telethon.tl.types import (
    DocumentAttributeFilename,
    MessageMediaDocument,
    MessageMediaPhoto,
    MessageMediaPoll,
    MessageMediaWebPage,
)


def normalize_channel_username(username: str) -> str:
    return username.strip().lstrip("@").lower()


def build_message_link(channel_username: str | None, channel_id: int, message_id: int) -> str | None:
    if channel_username:
        return f"https://t.me/{channel_username}/{message_id}"
    channel_id_str = str(channel_id)
    if channel_id_str.startswith("-100"):
        internal_id = channel_id_str[4:]
        return f"https://t.me/c/{internal_id}/{message_id}"
    return None


def detect_media_type(message) -> tuple[bool, str | None, int | None]:
    media = message.media
    if not media:
        return False, None, None

    if isinstance(media, MessageMediaPhoto):
        return True, "photo", None

    if isinstance(media, MessageMediaDocument) and media.document:
        doc = media.document
        mime = doc.mime_type or ""
        size = doc.size

        if mime.startswith("video/"):
            return True, "video", size
        if mime.startswith("audio/"):
            return True, "audio", size
        if mime == "image/gif":
            return True, "gif", size

        for attr in doc.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                ext = attr.file_name.rsplit(".", 1)[-1].lower()
                if ext in ("pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"):
                    return True, "document", size

        return True, "file", size

    if isinstance(media, MessageMediaPoll):
        return True, "poll", None

    if isinstance(media, MessageMediaWebPage):
        return True, "webpage", None

    return True, "other", None


def extract_reactions(message) -> list[tuple[str, int]]:
    reactions = []
    if not message.reactions or not message.reactions.results:
        return reactions

    for reaction_count in message.reactions.results:
        emoji = getattr(reaction_count.reaction, "emoticon", None)
        if emoji:
            reactions.append((emoji, reaction_count.count))

    return reactions


def extract_replies_count(message) -> int | None:
    if message.replies and message.replies.replies is not None:
        return message.replies.replies
    return None
