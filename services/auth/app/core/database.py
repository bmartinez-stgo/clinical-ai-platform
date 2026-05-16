import os

import aiosqlite

DB_PATH = os.getenv("DB_PATH", "/data/clients.db")

_CREATE_CLIENTS = """
CREATE TABLE IF NOT EXISTS clients (
    client_id    TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    secret_hash  TEXT NOT NULL,
    roles        TEXT NOT NULL DEFAULT '["user"]',
    enabled      INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT NOT NULL,
    last_used_at TEXT
)"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_CREATE_CLIENTS)
        await db.commit()
