"""
bot/handlers/referral.py — Referral program: deep-link, balance, stats.
"""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.menus import back_button

router = Router()


@router.callback_query(F.data == "menu:referral")
async def cb_referral(cb: CallbackQuery, db, bot: Bot) -> None:
    row = await db.fetchrow(
        """
        SELECT u.referral_code, u.referral_balance,
               COUNT(r.id) AS invite_count
        FROM   users u
        LEFT JOIN users r ON r.referred_by = u.id
        WHERE  u.id = $1
        GROUP BY u.referral_code, u.referral_balance
        """,
        cb.from_user.id,
    )

    me = await bot.get_me()
    ref_link = f"https://t.me/{me.username}?start=ref_{row['referral_code']}"

    text = (
        f"👥 <b>Referral Program</b>\n\n"
        f"Earn <b>10% lifetime commission</b> from every subscription\n"
        f"paid by users you invite.\n\n"
        f"{'─' * 28}\n"
        f"🔗 Your link:\n<code>{ref_link}</code>\n\n"
        f"👤 Invited users:  <b>{row['invite_count']}</b>\n"
        f"💰 Balance:        <b>${row['referral_balance']:.4f}</b>\n"
        f"{'─' * 28}\n\n"
        f"<i>Payouts are processed manually on request.\n"
        f"Contact @AlphaBotSupport to withdraw.</i>"
    )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=back_button())
    await cb.answer()
