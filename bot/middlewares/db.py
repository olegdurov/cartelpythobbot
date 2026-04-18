"""
bot/middlewares/db.py — Inject asyncpg connection per update.
"""
from __future__ import annotations
import os
from typing import Any, Awaitable, Callable

import asyncpg
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=os.environ["DATABASE_URL"].replace("+asyncpg", ""),
            min_size=2,
            max_size=10,
        )
    return _pool


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        pool = await get_pool()
        async with pool.acquire() as conn:
            data["db"] = conn
            return await handler(event, data)
