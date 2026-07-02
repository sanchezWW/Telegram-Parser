from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from app.telegram.client import tg_manager

router = APIRouter(prefix="/telegram", tags=["telegram"])

class ProxySchema(BaseModel):
    type: str = "socks5"   # socks5 или http
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None

class ConnectRequest(BaseModel):
    phone: str
    proxy: Optional[ProxySchema] = None

@router.post("/connect")
async def connect_account(request: ConnectRequest):
    try:
        proxy_dict = request.proxy.dict() if request.proxy else None
        client = await tg_manager.connect_and_login(
            phone=request.phone,
            proxy_config=proxy_dict
        )
        me = await client.get_me()
        return {
            "status": "success",
            "phone": request.phone,
            "user": {
                "id": me.id,
                "first_name": me.first_name,
                "username": me.username
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))