"""
bot/handlers/admin.py — Owner dashboard: stats, broadcast, user lookup, ban.
"""
import os
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards.menus import admin_menu, back_button
from bot.services.notifier import send_broadcast, NotifType

router   = Router()
ADMIN_ID = int(os.environ["ADMIN_ID"])


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


class BroadcastState(StatesGroup):
    waiting_text = State()


class LookupState(StatesGroup):
    waiting_id = State()


# ── Entry ──────────────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(msg: Message) -> None:
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("🛡 <b>Admin Dashboard</b>", parse_mode="HTML", reply_markup=admin_menu())


# ── Stats ──────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:stats")
async def cb_stats(cb: CallbackQuery, db) -> None:
    if not is_admin(cb.from_user.id):
        return
    row = await db.fetchrow(
        """
        SELECT
            (SELECT COUNT(*) FROM users)                                        AS total_users,
            (SELECT COUNT(*) FROM subscriptions WHERE status = 'active')        AS active_subs,
            (SELECT COUNT(*) FROM trades WHERE status = 'open')                 AS open_trades,
            (SELECT COALESCE(SUM(price_usd),0) FROM subscriptions)              AS total_revenue
        """
    )
    text = (
        f"📊 <b>Platform Stats</b>\n\n"
        f"👤 Total users:      <b>{row['total_users']}</b>\n"
        f"✅ Active subs:      <b>{row['active_subs']}</b>\n"
        f"📈 Open trades:      <b>{row['open_trades']}</b>\n"
        f"💵 Total revenue:    <b>${row['total_revenue']:.2f}</b>"
    )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=admin_menu())
    await cb.answer()


# ── Broadcast ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:broadcast")
async def cb_broadcast_start(cb: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(cb.from_user.id):
        return
    await cb.message.edit_text(
        "📢 <b>Broadcast</b>\n\nSend the message text to broadcast to all users.\n"
        "Supports HTML formatting.",
        parse_mode="HTML",
        reply_markup=back_button("admin:stats"),
    )
    await state.set_state(BroadcastState.waiting_text)
    await cb.answer()


@router.message(BroadcastState.waiting_text)
async def cb_broadcast_send(msg: Message, state: FSMContext, db, bot: Bot) -> None:
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    rows = await db.fetch("SELECT id FROM users WHERE is_banned = FALSE")
    user_ids = [r["id"] for r in rows]

    status_msg = await msg.answer(f"📤 Sending to {len(user_ids)} users…")
    result = await send_broadcast(bot, user_ids, msg.text, NotifType.BROADCAST)

    await status_msg.edit_text(
        f"✅ Broadcast complete\n"
        f"Sent: <b>{result['sent']}</b>  |  Failed: <b>{result['failed']}</b>",
        parse_mode="HTML",
    )


# ── User lookup ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:lookup")
async def cb_lookup_start(cb: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(cb.from_user.id):
        return
    await cb.message.edit_text(
        "🔍 Send the Telegram User ID to look up:",
        reply_markup=back_button(),
    )
    await state.set_state(LookupState.waiting_id)
    await cb.answer()


@router.message(LookupState.waiting_id)
async def cb_lookup_result(msg: Message, state: FSMContext, db) -> None:
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    try:
        uid = int(msg.text.strip())
    except ValueError:
        await msg.answer("⚠️ Invalid ID.")
        return

    row = await db.fetchrow(
        """
        SELECT u.*, s.status AS sub_status, s.expires_at
        FROM   users u
        LEFT JOIN subscriptions s ON s.user_id = u.id AND s.status = 'active'
        WHERE  u.id = $1
        """,
        uid,
    )
    if not row:
        await msg.answer("User not found.")
        return

    expires = row["expires_at"].strftime("%Y-%m-%d") if row["expires_at"] else "—"
    await msg.answer(
        f"👤 <b>User {uid}</b>\n"
        f"Name: {row['full_name']}\n"
        f"Lang: {row['language_code']}\n"
        f"Sub:  {row['sub_status'] or 'none'} (expires {expires})\n"
        f"Banned: {row['is_banned']}\n"
        f"Joined: {row['created_at'].strftime('%Y-%m-%d')}",
        parse_mode="HTML",
    )


# ── Ban / Unban ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.in_({"admin:ban", "admin:unban"}))
async def cb_ban(cb: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(cb.from_user.id):
        return
    action = cb.data.split(":")[1]
    await cb.message.edit_text(
        f"Send the user ID to <b>{'ban' if action == 'ban' else 'unban'}</b>:",
        parse_mode="HTML",
        reply_markup=back_button(),
    )
    await state.update_data(ban_action=action)
    await state.set_state(LookupState.waiting_id)
    await cb.answer()
