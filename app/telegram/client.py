import asyncio
import logging
from typing import Optional, Dict, Any
from telethon import TelegramClient
# ТРИ важных импорта для поддержки MTProto-подключений:
from telethon.network import ConnectionTcpMTProxyIntermediate, ConnectionTcpMTProxyAbridged
import socks 

logger = logging.getLogger(__name__)

class TelegramManager:
    def __init__(self):
        self.clients = {}
        self.lock = asyncio.Lock()

    def _prepare_proxy(self, proxy_config: Optional[Dict] = None):
        if not proxy_config:
            return None

        ptype = proxy_config.get("type", "").lower()

        # MTProto proxy возвращаем как кортеж (хост, порт, байты_секрета)
        if ptype == "mtproto":
            raw_secret = proxy_config.get('secret', '').strip()
            
            # Если это фейковый TLS (начинается с dd) и длина нечетная
            if raw_secret.startswith('dd') and len(raw_secret) % 2 != 0:
                # Дописываем ноль в конец для четности, чтобы hex скомпилировался
                raw_secret += '0'
            
            try:
                secret_bytes = bytes.fromhex(raw_secret)
            except ValueError:
                logger.error("Критическая ошибка: секрет содержит не-HEX символы!")
                secret_bytes = raw_secret.encode('utf-8')

            return (
                proxy_config['host'],
                int(proxy_config['port']),
                secret_bytes
            )

        # Обычный SOCKS5 / HTTP
        socks_type = socks.SOCKS5
        if ptype == "http":
            socks_type = socks.HTTP
        elif ptype == "socks4":
            socks_type = socks.SOCKS4

        return {
            'proxy_type': socks_type,
            'addr': proxy_config['host'],
            'port': int(proxy_config['port']),
            'username': proxy_config.get('username'),
            'password': proxy_config.get('password'),
            'rdns': True
        }


    async def get_client(self, phone: str, api_id=None, api_hash=None, proxy_config=None):
        async with self.lock:
            if phone in self.clients:
                return self.clients[phone]

            api_id = api_id or settings.API_ID
            api_hash = api_hash or settings.API_HASH

            session_path = f"sessions/{phone.replace('+', '')}"
            proxy = self._prepare_proxy(proxy_config)

            # Базовые аргументы для создания клиента
            client_kwargs = {
                "session": session_path,
                "api_id": api_id,
                "api_hash": api_hash,
                "connection_retries": 10,
                "retry_delay": 2,
                "timeout": 60
            }

            # Динамически меняем аргументы в зависимости от типа прокси
            if proxy_config and proxy_config.get("type", "").lower() == "mtproto":
                client_kwargs["connection"] = ConnectionTcpMTProxyIntermediate
                client_kwargs["proxy"] = proxy  # Передается кортеж (host, port, secret)
            else:
                client_kwargs["proxy"] = proxy  # Передается словарь или None

            client = TelegramClient(**client_kwargs)
            self.clients[phone] = client
            return client

    async def connect_and_login(self, phone: str, api_id=None, api_hash=None, proxy_config=None):
        client = await self.get_client(phone, api_id, api_hash, proxy_config)
        
        proxy_info = "MTProto" if proxy_config and proxy_config.get("type") == "mtproto" else "SOCKS5/HTTP"
        logger.info(f"Попытка подключения {phone} через {proxy_info}")
        
        for attempt in range(1, 7):
            try:
                await client.connect()
                logger.info("✅ Соединение установлено!")
                
                if not await client.is_user_authorized():
                    logger.info("Отправка кода авторизации...")
                    await client.send_code_request(phone, force_sms=True)
                    # Внимание: input() заблокирует весь асинхронный FastAPI сервер на время ввода кода. 
                    # Позже это нужно будет вынести во второй POST-метод API.
                    code = input(f"\nВведите код для {phone}: ")
                    await client.sign_in(phone, code)
                
                me = await client.get_me()
                logger.info(f"🎉 Успешно авторизован как {me.first_name} (@{me.username})")
                return client
                
            except Exception as e:
                logger.error(f"Попытка {attempt}/6 | {type(e).__name__}: {e}")
                await asyncio.sleep(4)
        
        raise Exception("Не удалось подключиться")

from app.core.config import settings
tg_manager = TelegramManager()