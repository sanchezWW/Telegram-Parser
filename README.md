# Telegram Parser API

Асинхронное веб-приложение на базе **FastAPI** и **Telethon** для авторизации Telegram-аккаунтов через прокси-серверы и последующего парсинга данных.

---

## 🛠️ Архитектура проекта

```text
TelegramParser/
├── app/
│   ├── core/
│   │   └── config.py        # Конфигурация и валидация настроек (Pydantic)
│   ├── telegram/
│   │   └── client.py        # Менеджер Telegram-клиентов (TelegramManager)
│   ├── models/              # Модели баз данных
│   ├── schemas/             # Схемы валидации запросов (Pydantic)
│   ├── routers/             # Эндпоинты FastAPI
│   └── utils/               # Вспомогательные утилиты
├── logs/                    # Логирование работы приложения
├── sessions/                # Хранение сессий авторизации (.session)
├── .env                     # Конфигурационные приватные ключи
├── run.py                   # Точка запуска веб-сервера Uvicorn
└── test_api.py              # Скрипт автоматического тестирования API
```

---

## 🚀 Быстрый запуск

### 1. Подготовка окружения
Убедитесь, что у вас установлен Python версии 3.10 или выше. Выполните инициализацию изолированной среды:

```powershell
# Создание виртуального окружения
python -m venv .venv

# Активация окружения (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Установка всех необходимых зависимостей
python -m pip install pydantic-settings python-dotenv fastapi uvicorn telethon python-socks[asyncio] PySocks requests
```

### 2. Настройка переменных окружения
Создайте файл `.env` в корневой директории проекта и добавьте туда свои данные разработчика, полученные на платформе [my.telegram.org](https://telegram.org):

```env
API_ID=12345678
API_HASH=your_api_hash_string_here
```

### 3. Запуск веб-сервера
Запустите основной процесс приложения:
```powershell
python run.py
```
После запуска интерактивная документация API (Swagger UI) станет доступна по адресу: `http://127.0.0`.

---

## 📡 Использование API

### Инициализация подключения (POST `/telegram/connect`)

Для создания новой сессии и отправки запроса кода авторизации необходимо отправить POST-запрос с конфигурацией прокси.

#### Пример запроса через PowerShell:
```powershell
\$body = @{
    phone = "+79001234567"
    proxy = @{
        type     = "socks5"       # Поддерживаются: socks5, http, mtproto
        host     = "185.233.100.5" # IP-адрес или домен вашего прокси
        port     = 1080
        username = "proxy_user"    # Оставьте "", если прокси без авторизации
        password = "proxy_password" # Оставьте "", если прокси без авторизации
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:8000/telegram/connect" -Method Post -ContentType "application/json" -Body \$body
```

#### Важное примечание:
При первом подключении в консоли запущенного сервера `run.py` появится интерактивный запрос `Введите код для +79001234567:`. Введите код, пришедший в ваше официальное приложение Telegram, чтобы завершить привязку аккаунта. Файл сессии сохранится в директорию `sessions/`.