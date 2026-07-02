from fastapi import FastAPI
from app.core.config import settings
from app.routers.telegram import router as telegram_router
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="Telegram Parser & Sender", debug=settings.DEBUG)

# Подключаем роутеры
app.include_router(telegram_router)

@app.get("/")
async def root():
    return {"message": "Сервис Telegram Parser запущен!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)