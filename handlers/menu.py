"""
bot/handlers/menu.py — Main menu navigation and risk level selector.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards.menus import main_menu, risk_selector
from bot.services.user_service import get_user_lang
from bot.services.subscription_service import has_active_subscription
from bot.services.trading_service import set_risk_level

router = Router()

WELCOME = {
    "en": "👋 <b>AlphaBot</b> — your automated crypto edge.\n\nChoose an action:",
    "ru": "👋 <b>AlphaBot</b> — ваш автоматический трейдер.\n\nВыберите действие:",
    "ua": "👋 <b>AlphaBot</b> — ваш автоматичний трейдер.\n\nОберіть дію:",
    "de": "👋 <b>AlphaBot</b> — Ihr automatisierter Trader.\n\nAktion wählen:",
    "es": "👋 <b>AlphaBot</b> — tu trader automático.\n\nElige una acción:",
    "fr": "👋 <b>AlphaBot</b> — votre trader automatisé.\n\nChoisissez une action:",
}


@router.callback_query(F.data == "menu:main")
async def cb_main_menu(cb: CallbackQuery, db) -> None:
    lang = await get_user_lang(db, cb.from_user.id)
    await cb.message.edit_text(
        WELCOME.get(lang, WELCOME["en"]),
        parse_mode="HTML",
        reply_markup=main_menu(lang),
    )
    await cb.answer()


@router.callback_query(F.data == "menu:trading")
async def cb_trading(cb: CallbackQuery, db) -> None:
    active = await has_active_subscription(db, cb.from_user.id)
    if not active:
        await cb.answer("⚠️ No active subscription.", show_alert=True)
        return
    await cb.message.edit_text(
        "📊 <b>Risk level</b>\n\n"
        "Select how aggressively the algorithm trades.\n"
        "<i>Higher risk = larger position size and wider stops.</i>",
        parse_mode="HTML",
        reply_markup=risk_selector(),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("risk:"))
async def cb_risk(cb: CallbackQuery, db) -> None:
    level = int(cb.data.split(":")[1])
    await set_risk_level(db, cb.from_user.id, level)
    labels = {
        1: "Conservative 🛡",
        2: "Moderate 📊",
        3: "Balanced ⚖️",
        4: "Aggressive 🔥",
        5: "Depo Overdrive 💀",
    }
    await cb.answer(f"✅ {labels[level]} activated", show_alert=True)


@router.callback_query(F.data == "menu:settings")
async def cb_settings(cb: CallbackQuery, db) -> None:
    from bot.keyboards.menus import language_selector
    await cb.message.edit_text(
        "⚙️ <b>Settings</b>\n\nChoose your language:",
        parse_mode="HTML",
        reply_markup=language_selector(),
    )
    await cb.answer()


@router.callback_query(F.data == "menu:support")
async def cb_support(cb: CallbackQuery) -> None:
    await cb.message.edit_text(
        "🆘 <b>Support</b>\n\n"
        "Contact us: @AlphaBotSupport\n"
        "Response time: within 24 hours.",
        parse_mode="HTML",
    )
    await cb.answer()
