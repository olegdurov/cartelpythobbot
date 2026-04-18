"""
bot/handlers/billing.py — Subscription purchase via CryptoBot, Stars, Wallet.
"""
import os
from datetime import datetime, timedelta, timezone

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery

from bot.keyboards.menus import billing_menu, back_button
from bot.services.subscription_service import create_subscription, get_subscription_info
from bot.services.referral_service import pay_referral_commission

router = Router()

PRICE_USD  = float(os.environ.get("SUBSCRIPTION_PRICE_USD", "30.00"))
STARS_PRICE = 600  # Telegram Stars equivalent (~$30)


@router.callback_query(F.data == "menu:billing")
async def cb_billing(cb: CallbackQuery, db) -> None:
    info = await get_subscription_info(db, cb.from_user.id)
    if info and info["status"] == "active":
        expires = info["expires_at"].strftime("%Y-%m-%d")
        text = (
            f"💳 <b>Subscription</b>\n\n"
            f"Status: ✅ Active\n"
            f"Expires: <b>{expires}</b>\n\n"
            f"Renew early to extend your period."
        )
    else:
        text = (
            f"💳 <b>Subscription</b>\n\n"
            f"Status: ❌ Inactive\n"
            f"Price: <b>${PRICE_USD:.2f} / month</b>\n\n"
            f"Choose a payment method:"
        )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=billing_menu())
    await cb.answer()


# ── CryptoBot ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "pay:cryptobot")
async def pay_cryptobot(cb: CallbackQuery) -> None:
    # CryptoBot invoice creation via their API
    # See: https://help.crypt.bot/crypto-pay-api
    import aiohttp
    token = os.environ["CRYPTOBOT_TOKEN"]
    async with aiohttp.ClientSession() as s:
        resp = await s.post(
            "https://pay.crypt.bot/api/createInvoice",
            headers={"Crypto-Pay-API-Token": token},
            json={
                "asset": "USDT",
                "amount": str(PRICE_USD),
                "description": "AlphaBot subscription — 30 days",
                "payload": str(cb.from_user.id),
                "expires_in": 3600,
            },
        )
        data = await resp.json()

    if data.get("ok"):
        invoice = data["result"]
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="💳 Pay with CryptoBot", url=invoice["pay_url"])
        ]])
        await cb.message.edit_text(
            f"💳 <b>CryptoBot Payment</b>\n\n"
            f"Amount: <b>{PRICE_USD} USDT</b>\n"
            f"Invoice expires in 60 minutes.\n\n"
            f"After payment, your subscription activates automatically.",
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        await cb.answer("⚠️ Could not create invoice. Try again later.", show_alert=True)

    await cb.answer()


# ── Telegram Stars ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "pay:stars")
async def pay_stars(cb: CallbackQuery, bot: Bot) -> None:
    await bot.send_invoice(
        chat_id      = cb.from_user.id,
        title        = "AlphaBot Subscription",
        description  = "30-day access to automated crypto trading",
        payload      = f"sub_{cb.from_user.id}",
        currency     = "XTR",
        prices       = [LabeledPrice(label="Subscription", amount=STARS_PRICE)],
    )
    await cb.answer()


@router.pre_checkout_query()
async def pre_checkout(pq: PreCheckoutQuery) -> None:
    await pq.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(msg: Message, db) -> None:
    user_id  = msg.from_user.id
    provider = "stars"
    pay_ref  = msg.successful_payment.telegram_payment_charge_id

    await create_subscription(db, user_id, provider, pay_ref)
    await pay_referral_commission(db, user_id, PRICE_USD)

    await msg.answer(
        "🎉 <b>Payment confirmed!</b>\n\n"
        "Your 30-day subscription is now active.\n"
        "Use /start to begin trading.",
        parse_mode="HTML",
    )
