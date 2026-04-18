"""
bot/middlewares/subscription.py — Gate new-trade actions behind active subscription.
Existing open trades are never force-closed.
"""
from __future__ import annotations
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery

# Callbacks that require an active subscription
GATED_CALLBACKS = {"menu:trading", *{f"risk:{i}" for i in range(1, 6)}}


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, CallbackQuery) and event.data in GATED_CALLBACKS:
            db = data.get("db")
            if db:
                from bot.services.subscription_service import has_active_subscription
                active = await has_active_subscription(db, event.from_user.id)
                if not active:
                    await event.answer(
                        "⚠️ Active subscription required to start new trades.",
                        show_alert=True,
                    )
                    return   # block handler, existing trades keep running
        return await handler(event, data)
