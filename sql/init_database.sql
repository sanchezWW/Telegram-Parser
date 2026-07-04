-- ============================================================
-- TelegramParser — скрипт создания базы данных для SSMS
-- Выполните этот скрипт в SQL Server Management Studio
-- ============================================================

-- 1. Создание базы данных
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'TelegramParser')
BEGIN
    CREATE DATABASE TelegramParser;
END
GO

USE TelegramParser;
GO

-- 2. Таблица каналов
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'channels')
BEGIN
    CREATE TABLE channels (
        id              BIGINT          NOT NULL PRIMARY KEY,
        username        NVARCHAR(255)   NULL,
        title           NVARCHAR(512)   NOT NULL,
        about           NVARCHAR(MAX)   NULL,
        participants_count INT          NULL,
        is_verified     BIT             NOT NULL DEFAULT 0,
        is_broadcast    BIT             NOT NULL DEFAULT 1,
        linked_chat_id  BIGINT          NULL,
        scraped_at      DATETIME2       NOT NULL DEFAULT GETUTCDATE(),
        updated_at      DATETIME2       NOT NULL DEFAULT GETUTCDATE()
    );
    CREATE INDEX ix_channels_username ON channels (username);
END
GO

-- 3. Таблица сообщений
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'messages')
BEGIN
    CREATE TABLE messages (
        id              INT             IDENTITY(1,1) PRIMARY KEY,
        channel_id      BIGINT          NOT NULL,
        message_id      INT             NOT NULL,
        text            NVARCHAR(MAX)   NULL,
        date            DATETIME2       NOT NULL,
        edit_date       DATETIME2       NULL,
        views           INT             NULL,
        forwards        INT             NULL,
        replies         INT             NULL,
        has_media       BIT             NOT NULL DEFAULT 0,
        media_type      NVARCHAR(50)    NULL,
        media_size      BIGINT          NULL,
        grouped_id      BIGINT          NULL,
        post_author     NVARCHAR(255)   NULL,
        is_pinned       BIT             NOT NULL DEFAULT 0,
        link            NVARCHAR(512)   NULL,
        scraped_at      DATETIME2       NOT NULL DEFAULT GETUTCDATE(),
        CONSTRAINT fk_messages_channel FOREIGN KEY (channel_id) REFERENCES channels(id),
        CONSTRAINT uq_channel_message UNIQUE (channel_id, message_id)
    );
    CREATE INDEX ix_messages_channel_id ON messages (channel_id);
    CREATE INDEX ix_messages_message_id ON messages (message_id);
    CREATE INDEX ix_messages_date ON messages (date);
END
GO

-- 4. Таблица реакций
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'message_reactions')
BEGIN
    CREATE TABLE message_reactions (
        id              INT             IDENTITY(1,1) PRIMARY KEY,
        message_id      INT             NOT NULL,
        emoji           NVARCHAR(64)    NOT NULL,
        count           INT             NOT NULL DEFAULT 0,
        CONSTRAINT fk_reactions_message FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
        CONSTRAINT uq_message_reaction UNIQUE (message_id, emoji)
    );
    CREATE INDEX ix_message_reactions_message_id ON message_reactions (message_id);
END
GO

-- 5. Таблица задач парсинга
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'parse_jobs')
BEGIN
    CREATE TABLE parse_jobs (
        id                  INT             IDENTITY(1,1) PRIMARY KEY,
        channel_id          BIGINT          NULL,
        channel_username    NVARCHAR(255)   NOT NULL,
        phone               NVARCHAR(20)    NOT NULL,
        status              NVARCHAR(20)    NOT NULL DEFAULT 'pending',
        messages_limit      INT             NOT NULL DEFAULT 100,
        messages_parsed     INT             NOT NULL DEFAULT 0,
        messages_new        INT             NOT NULL DEFAULT 0,
        messages_updated    INT             NOT NULL DEFAULT 0,
        error_message       NVARCHAR(MAX)   NULL,
        started_at          DATETIME2       NOT NULL DEFAULT GETUTCDATE(),
        finished_at         DATETIME2       NULL,
        CONSTRAINT fk_parse_jobs_channel FOREIGN KEY (channel_id) REFERENCES channels(id)
    );
    CREATE INDEX ix_parse_jobs_channel_id ON parse_jobs (channel_id);
    CREATE INDEX ix_parse_jobs_status ON parse_jobs (status);
END
GO

PRINT 'База данных TelegramParser успешно создана!';
