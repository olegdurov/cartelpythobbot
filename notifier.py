"""
bot/services/notifier.py — Visual notification dispatcher.

Maps event type → asset image + formatted caption.
Handles single-user trade alerts and mass broadcast.
"""
from __future__ import annotations

import asyncio
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Iterable

from aiogram import Bot
from aiogram.types import FSInputFile

logger = logging.getLogger(__name__)

ASSETS = Path("assets")
ADMIN_ID = int(os.environ["ADMIN_ID"])


class NotifType(Enum):
    TAKE_PROFIT = "take_profit"
    STOP_LOSS   = "stop_loss"
    BROADCAST   = "broadcast"
    SYSTEM      = "system"


_ASSET_MAP: dict[NotifType, str] = {
    NotifType.TAKE_PROFIT: "chart_up.png",
    NotifType.STOP_LOSS:   "chart_down.png",
    NotifType.BROADCAST:   "money_bag.png",
    NotifType.SYSTEM:      "money_bag.png",
}

_EMOJI_MAP: dict[NotifType, str] = {
    NotifType.TAKE_PROFIT: "✅",
    NotifType.STOP_LOSS:   "🔴",
    NotifType.BROADCAST:   "📢",
    NotifType.SYSTEM:      "⚙️",
}


def _trade_caption(
    notif_type: NotifType,
    symbol: str,
    pnl_pct: float,
    exchange: str,
    risk_level: int,
) -> str:
    emoji     = _EMOJI_MAP[notif_type]
    direction = "Take Profit" if notif_type == NotifType.TAKE_PROFIT else "Stop Loss"
    sign      = "+" if pnl_pct >= 0 else ""
    return (
        f"{emoji} <b>{direction}</b>  |  <code>{symbol}</code>\n"
        f"{'─' * 28}\n"
        f"📊 Exchange    <b>{exchange.capitalize()}</b>\n"
        f"⚡ Risk level  <b>{risk_level} / 5</b>\n"
        f"💹 Result      <b>{sign}{pnl_pct:.2f}%</b>\n"
        f"{'─' * 28}\n"
        f"<i>Powered by AlphaBot</i>"
    )


async def send_trade_notification(
    bot: Bot,
    user_id: int,
    notif_type: NotifType,
    *,
    symbol: str,
    pnl_pct: float,
    exchange: str,
    risk_level: int,
) -> None:
    asset   = ASSETS / _ASSET_MAP[notif_type]
    caption = _trade_caption(notif_type, symbol, pnl_pct, exchange, risk_level)
    try:
        await bot.send_photo(
            chat_id    = user_id,
            photo      = FSInputFile(asset),
            caption    = caption,
            parse_mode = "HTML",
        )
    except Exception as e:
        logger.warning("Failed to notify user %s: %s", user_id, e)


async def send_broadcast(
    bot: Bot,
    user_ids: Iterable[int],
    text: str,
    notif_type: NotifType = NotifType.BROADCAST,
    delay: float = 0.05,   # ~20 msgs/sec — stays within Telegram limits
) -> dict[str, int]:
    asset = ASSETS / _ASSET_MAP[notif_type]
    ok = fail = 0

    for uid in user_ids:
        try:
            await bot.send_photo(
                chat_id    = uid,
                photo      = FSInputFile(asset),
                caption    = text,
                parse_mode = "HTML",
            )
            ok += 1
        except Exception as e:
            logger.warning("Broadcast skip user %s: %s", uid, e)
            fail += 1
        await asyncio.sleep(delay)

    return {"sent": ok, "failed": fail}


async def notify_admin_keys_added(bot: Bot, tg_user, exchange: str) -> None:
    """Event-only admin alert — no secrets exposed."""
    text = (
        f"🔔 <b>New API keys bound</b>\n"
        f"👤 User: <a href='tg://user?id={tg_user.id}'>{tg_user.full_name}</a> "
        f"(<code>{tg_user.id}</code>)\n"
        f"🏦 Exchange: <b>{exchange.capitalize()}</b>"
    )
    try:
        await bot.send_message(ADMIN_ID, text, parse_mode="HTML")
    except Exception as e:
        logger.warning("Admin notify failed: %s", e)


async def notify_admin_new_user(bot: Bot, tg_user) -> None:
    text = (
        f"👋 <b>New user registered</b>\n"
        f"👤 <a href='tg://user?id={tg_user.id}'>{tg_user.full_name}</a> "
        f"(<code>{tg_user.id}</code>)"
    )
    try:
        await bot.send_message(ADMIN_ID, text, parse_mode="HTML")
    except Exception as e:
        logger.warning("Admin new-user notify failed: %s", e)
