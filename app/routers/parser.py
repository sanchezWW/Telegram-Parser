from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.models import Channel, Message, ParseJob
from app.database.session import get_db
from app.schemas.parser import (
    ChannelSchema,
    ChannelStatsSchema,
    MessageSchema,
    ParseChannelRequest,
    ParseJobSchema,
)
from app.services.parser import parser_service

router = APIRouter(prefix="/parser", tags=["parser"])


@router.post("/channel", response_model=ParseJobSchema)
async def parse_channel(request: ParseChannelRequest, db: Session = Depends(get_db)):
    """Парсинг канала: метаданные + последние N постов с метриками."""
    try:
        proxy_dict = request.proxy.model_dump() if request.proxy else None
        job = await parser_service.parse_channel(
            db=db,
            phone=request.phone,
            channel_username=request.channel,
            limit=request.limit,
            proxy_config=proxy_dict,
        )
        return job
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/jobs", response_model=list[ParseJobSchema])
def list_parse_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return (
        db.query(ParseJob)
        .order_by(ParseJob.started_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/jobs/{job_id}", response_model=ParseJobSchema)
def get_parse_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(ParseJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return job


@router.get("/channels", response_model=list[ChannelSchema])
def list_channels(db: Session = Depends(get_db)):
    channels = db.query(Channel).order_by(Channel.updated_at.desc()).all()
    result = []
    for channel in channels:
        msg_count = db.query(Message).filter(Message.channel_id == channel.id).count()
        data = ChannelSchema.model_validate(channel)
        data.messages_count = msg_count
        result.append(data)
    return result


@router.get("/channels/{channel_id}", response_model=ChannelSchema)
def get_channel(channel_id: int, db: Session = Depends(get_db)):
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Канал не найден")
    data = ChannelSchema.model_validate(channel)
    data.messages_count = db.query(Message).filter(Message.channel_id == channel_id).count()
    return data


@router.get("/channels/{channel_id}/messages", response_model=list[MessageSchema])
def get_channel_messages(
    channel_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    if not db.get(Channel, channel_id):
        raise HTTPException(status_code=404, detail="Канал не найден")

    return (
        db.query(Message)
        .filter(Message.channel_id == channel_id)
        .order_by(Message.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/channels/{channel_id}/stats", response_model=ChannelStatsSchema)
def get_channel_stats(channel_id: int, db: Session = Depends(get_db)):
    try:
        return parser_service.get_channel_stats(db, channel_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
