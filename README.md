# Telegram Channel Parser

Асинхронное веб-приложение на **FastAPI** + **Telethon** для авторизации Telegram-аккаунтов и парсинга публичных каналов с сохранением данных в **Microsoft SQL Server**.

## Что парсится


| Сущность            | Данные                                                                  |
| ------------------- | ----------------------------------------------------------------------- |
| **Канал**           | название, username, описание, число подписчиков, верификация            |
| **Сообщения**       | текст, дата, просмотры, репосты, комментарии, медиа-тип, ссылка на пост |
| **Реакции**         | emoji и количество                                                      |
| **Задачи парсинга** | статус, сколько новых/обновлённых постов                                |


Повторный парсинг обновляет метрики (views, forwards) у уже сохранённых постов — удобно для отслеживания динамики.

---

## Архитектура

```text
TelegramParser/
├── app/
│   ├── core/config.py          # Настройки (.env)
│   ├── database/
│   │   ├── models.py           # ORM-модели SQLAlchemy
│   │   └── session.py          # Подключение к SQL Server
│   ├── services/parser.py      # Логика парсинга Telethon
│   ├── routers/
│   │   ├── telegram.py         # Авторизация аккаунта
│   │   └── parser.py           # API парсера
│   ├── schemas/parser.py       # Pydantic-схемы
│   └── utils/telegram_helpers.py
├── sql/init_database.sql       # Скрипт для SSMS
├── scripts/init_db.py          # Создание таблиц через Python
├── sessions/                   # Файлы сессий Telethon
├── .env.example
└── run.py
```

---

## Быстрый старт

### 1. Python-окружение

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Настройка `.env`

Скопируйте `.env.example` в `.env` и заполните:

```env
API_ID=12345678
API_HASH=your_api_hash_here

# Имя сервера — как в SSMS при подключении
MSSQL_SERVER=localhost\SQLEXPRESS
MSSQL_DATABASE=TelegramParser
MSSQL_DRIVER=ODBC Driver 17 for SQL Server
MSSQL_TRUSTED_CONNECTION=True
```

Ключи `API_ID` и `API_HASH` получите на [my.telegram.org](https://my.telegram.org).

---

## Настройка SQL Server (для новичков)

### Шаг 1. Установка SQL Server

1. Скачайте **SQL Server Express** (бесплатно): [Microsoft SQL Server Downloads](https://www.microsoft.com/sql-server/sql-server-downloads)
2. При установке выберите режим **Basic** или **Custom** с компонентом **Database Engine**
3. Запомните имя экземпляра — по умолчанию `localhost` или `localhost\SQLEXPRESS`

### Шаг 2. SQL Server Management Studio (SSMS)

1. Скачайте SSMS: [Download SSMS](https://learn.microsoft.com/sql/ssms/download-sql-server-management-studio-ssms)
2. Запустите SSMS → **Connect** → Server name: `localhost` (или `localhost\SQLEXPRESS`)
3. Authentication: **Windows Authentication** (проще для начала)

### Шаг 3. Создание базы данных

**Вариант A — через SSMS (рекомендуется для обучения):**

1. В SSMS: **File → Open → File** → выберите `sql/init_database.sql`
2. Нажмите **Execute** (F5)
3. В Object Explorer появится база `TelegramParser` с таблицами

**Вариант B — через Python:**

```powershell
python scripts/create_database.py   # создать базу
python scripts/init_db.py           # создать таблицы
```

> Таблицы также создаются автоматически при первом запуске сервера.

### Шаг 4. ODBC-драйвер

Python подключается к SQL Server через ODBC. Установите драйвер:

[Microsoft ODBC Driver 17 for SQL Server](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server)

Проверка в PowerShell:

```powershell
Get-OdbcDriver | Where-Object Name -like "*SQL Server*"
```

### Шаг 5. Настройка подключения в `.env`

Смотрите имя сервера в SSMS при подключении — у **SQL Server Express** это почти всегда `localhost\SQLEXPRESS`, а не просто `localhost`.

```env
MSSQL_SERVER=localhost\SQLEXPRESS
MSSQL_DATABASE=TelegramParser
MSSQL_TRUSTED_CONNECTION=True
```

**SQL Authentication** (логин `sa` + пароль):

```env
MSSQL_TRUSTED_CONNECTION=False
MSSQL_USERNAME=sa
MSSQL_PASSWORD=YourStrongPassword
```

### Шаг 6. Проверка в SSMS

После парсинга канала выполните в SSMS:

```sql
USE TelegramParser;

SELECT TOP 10 c.title, m.message_id, m.views, m.forwards, m.date
FROM messages m
JOIN channels c ON c.id = m.channel_id
ORDER BY m.date DESC;
```

---

## Запуск

```powershell
python run.py
```

Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---



### Как парсить

---

### Шаг 1. Запустить сервер

```powershell
.venv\Scripts\Activate.ps1
python run.py
```

Оставь это окно открытым — здесь же появится запрос кода Telegram при первой авторизации.

---

### Шаг 2. Авторизовать Telegram-аккаунт (один раз)

Нужен **реальный** номер телефона, привязанный к Telegram. Прокси — только если без него Telegram не открывается.

#### Через Swagger

1. Открой [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
2. Раздел **telegram** → `POST /telegram/connect` → **Try it out**
3. Тело запроса (без прокси):

```json
{
  "phone": "+79001234567"
}
```

1. **Execute**
2. В **консоли**, где запущен `run.py`, введи код из Telegram (и пароль 2FA, если включён)
3. В ответе будет `"status": "success"` — сессия сохранена в папку `sessions/`

#### Через PowerShell

```powershell
$body = @{ phone = "+79001234567" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/telegram/connect" `
    -Method Post -ContentType "application/json" -Body $body
```

> Повторная авторизация не нужна, пока файл сессии в `sessions/` не удалён.

---

### Шаг 3. Спарсить канал

Парсятся только **публичные** каналы, к которым у аккаунта есть доступ. Username — без `@`.

Примеры каналов для демо:


| Username   | Описание                   |
| ---------- | -------------------------- |
| `durov`    | Канал Павла Дурова         |
| `telegram` | Официальный канал Telegram |
| `tproger`  | IT-новости                 |


#### Через Swagger

1. `POST /parser/channel` → **Try it out**
2. Тело запроса:

```json
{
  "phone": "+79001234567",
  "channel": "durov",
  "limit": 50
}
```


| Поле      | Описание                                  |
| --------- | ----------------------------------------- |
| `phone`   | Тот же номер, что при `/telegram/connect` |
| `channel` | Username канала без `@`                   |
| `limit`   | Сколько последних постов забрать (1–1000) |


1. **Execute** — парсинг может занять от нескольких секунд до минуты

Пример успешного ответа:

```json
{
  "id": 1,
  "channel_username": "durov",
  "status": "completed",
  "messages_parsed": 50,
  "messages_new": 50,
  "messages_updated": 0,
  "messages_limit": 50
}
```

#### Через PowerShell

```powershell
$body = @{
    phone   = "+79001234567"
    channel = "durov"
    limit   = 50
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/parser/channel" `
    -Method Post -ContentType "application/json" -Body $body
```

---

### Шаг 4. Посмотреть результат

#### В Swagger / браузере


| Действие                           | Эндпоинт                                     |
| ---------------------------------- | -------------------------------------------- |
| Список каналов в БД                | `GET /parser/channels`                       |
| Посты канала                       | `GET /parser/channels/{channel_id}/messages` |
| Статистика (avg views, топ постов) | `GET /parser/channels/{channel_id}/stats`    |
| История парсингов                  | `GET /parser/jobs`                           |


`channel_id` — числовой ID из ответа `GET /parser/channels`, не username.

#### В SQL Server Management Studio

```sql
USE TelegramParser;

-- Какие каналы уже в базе
SELECT id, username, title, participants_count FROM channels;

-- Последние 10 постов с метриками
SELECT TOP 10
    c.title,
    m.message_id,
    m.views,
    m.forwards,
    m.date,
    m.link
FROM messages m
JOIN channels c ON c.id = m.channel_id
ORDER BY m.date DESC;

-- Топ постов по просмотрам
SELECT TOP 5 message_id, views, forwards, LEFT(text, 80) AS preview
FROM messages
WHERE channel_id = 1  -- замени на свой channel_id
ORDER BY views DESC;
```

---

### Шаг 5. Повторный парсинг

Запусти `POST /parser/channel` с тем же каналом ещё раз:

- новые посты → `messages_new` увеличится
- старые посты → обновятся `views`, `forwards`, реакции (`messages_updated`)

Так можно отслеживать, как растут просмотры у одних и тех же постов.

---

### Частые ошибки


| Ошибка                   | Причина                               | Решение                                   |
| ------------------------ | ------------------------------------- | ----------------------------------------- |
| `Аккаунт не авторизован` | Не вызывали `/telegram/connect`       | Авторизуйся (шаг 2)                       |
| `Канал недоступен`       | Приватный канал или неверный username | Проверь, что канал публичный              |
| Код не приходит          | —                                     | Смотри консоль `run.py`, код вводится там |
| Долго выполняется        | Много постов / медленная сеть         | Уменьши `limit` до 20–50                  |


---

## API (справочник)

### 1. Авторизация аккаунта

```http
POST /telegram/connect
```

```json
{
  "phone": "+79001234567",
  "proxy": {
    "type": "socks5",
    "host": "127.0.0.1",
    "port": 1080
  }
}
```

При первом входе код запрашивается в консоли сервера. Сессия сохраняется в `sessions/`.

### 2. Парсинг канала

```http
POST /parser/channel
```

```json
{
  "phone": "+79001234567",
  "channel": "durov",
  "limit": 100
}
```

Пример через PowerShell:

```powershell
$body = @{
    phone   = "+79001234567"
    channel = "durov"
    limit   = 50
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/parser/channel" `
    -Method Post -ContentType "application/json" -Body $body
```

### 3. Остальные эндпоинты


| Метод | URL                              | Описание                                 |
| ----- | -------------------------------- | ---------------------------------------- |
| GET   | `/parser/jobs`                   | История задач парсинга                   |
| GET   | `/parser/jobs/{id}`              | Детали задачи                            |
| GET   | `/parser/channels`               | Список спарсенных каналов                |
| GET   | `/parser/channels/{id}/messages` | Сообщения канала                         |
| GET   | `/parser/channels/{id}/stats`    | Статистика: avg views, топ постов, медиа |


---

## Требования

- Python 3.10+
- SQL Server 2019+ (Express подойдёт)
- ODBC Driver 17 for SQL Server
- API-ключи Telegram ([my.telegram.org](https://my.telegram.org))

