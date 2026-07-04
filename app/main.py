from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.core.config import settings
from app.database.session import Base, engine
from app.routers.parser import router as parser_router
from app.routers.telegram import router as telegram_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


import logging

from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Подключение к SQL Server установлено, таблицы готовы")
    except OperationalError as exc:
        logger.error(
            "Не удалось подключиться к SQL Server. "
            "Проверьте MSSQL_SERVER в .env (для Express: localhost\\SQLEXPRESS). "
            "Ошибка: %s",
            exc.orig if hasattr(exc, "orig") else exc,
        )
        raise
    yield


app = FastAPI(
    title="Telegram Channel Parser",
    description="Парсер Telegram-каналов с сохранением в SQL Server",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.include_router(telegram_router)
app.include_router(parser_router)

@app.get("/")
async def root():
    return {"message": "Сервис Telegram Parser запущен!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)