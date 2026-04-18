"""
bot/keyboards/menus.py — All inline keyboards
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

LANGS = {
    "en": {
        "trading":  "📈 Trading",
        "keys":     "🔑 API Keys",
        "billing":  "💳 Billing",
        "referral": "👥 Referral",
        "settings": "⚙️ Settings",
        "support":  "🆘 Support",
    },
    "ru": {
        "trading":  "📈 Трейдинг",
        "keys":     "🔑 API Ключи",
        "billing":  "💳 Оплата",
        "referral": "👥 Реферал",
        "settings": "⚙️ Настройки",
        "support":  "🆘 Поддержка",
    },
    "ua": {
        "trading":  "📈 Трейдинг",
        "keys":     "🔑 API Ключі",
        "billing":  "💳 Оплата",
        "referral": "👥 Реферал",
        "settings": "⚙️ Налаштування",
        "support":  "🆘 Підтримка",
    },
    "de": {
        "trading":  "📈 Trading",
        "keys":     "🔑 API-Schlüssel",
        "billing":  "💳 Abrechnung",
        "referral": "👥 Empfehlung",
        "settings": "⚙️ Einstellungen",
        "support":  "🆘 Support",
    },
    "es": {
        "trading":  "📈 Trading",
        "keys":     "🔑 Claves API",
        "billing":  "💳 Facturación",
        "referral": "👥 Referido",
        "settings": "⚙️ Ajustes",
        "support":  "🆘 Soporte",
    },
    "fr": {
        "trading":  "📈 Trading",
        "keys":     "🔑 Clés API",
        "billing":  "💳 Facturation",
        "referral": "👥 Parrainage",
        "settings": "⚙️ Paramètres",
        "support":  "🆘 Support",
    },
}


def main_menu(lang: str = "en") -> InlineKeyboardMarkup:
    t = LANGS.get(lang, LANGS["en"])
    b = InlineKeyboardBuilder()
    b.button(text=t["trading"],  callback_data="menu:trading")
    b.button(text=t["keys"],     callback_data="menu:keys")
    b.button(text=t["billing"],  callback_data="menu:billing")
    b.button(text=t["referral"], callback_data="menu:referral")
    b.button(text=t["settings"], callback_data="menu:settings")
    b.button(text=t["support"],  callback_data="menu:support")
    b.adjust(2, 2, 2)
    return b.as_markup()


def risk_selector() -> InlineKeyboardMarkup:
    levels = [
        ("1 — Conservative 🛡",   "risk:1"),
        ("2 — Moderate 📊",       "risk:2"),
        ("3 — Balanced ⚖️",       "risk:3"),
        ("4 — Aggressive 🔥",     "risk:4"),
        ("5 — Depo Overdrive 💀", "risk:5"),
    ]
    b = InlineKeyboardBuilder()
    for label, cb in levels:
        b.button(text=label, callback_data=cb)
    b.button(text="◀ Back", callback_data="menu:main")
    b.adjust(1)
    return b.as_markup()


def language_selector() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    langs = [
        ("🇬🇧 English",    "lang:en"),
        ("🇷🇺 Русский",    "lang:ru"),
        ("🇺🇦 Українська", "lang:ua"),
        ("🇩🇪 Deutsch",    "lang:de"),
        ("🇪🇸 Español",    "lang:es"),
        ("🇫🇷 Français",   "lang:fr"),
    ]
    for label, cb in langs:
        b.button(text=label, callback_data=cb)
    b.adjust(2)
    return b.as_markup()


def exchange_selector() -> InlineKeyboardMarkup:
    exchanges = ["Binance", "OKX", "Bybit", "KuCoin", "Gate.io"]
    b = InlineKeyboardBuilder()
    for ex in exchanges:
        b.button(text=ex, callback_data=f"bind:{ex.lower().replace('.', '')}")
    b.button(text="◀ Back", callback_data="menu:main")
    b.adjust(2)
    return b.as_markup()


def billing_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="💎 Pay with CryptoBot", callback_data="pay:cryptobot")
    b.button(text="⭐ Pay with Stars",     callback_data="pay:stars")
    b.button(text="👛 Telegram Wallet",    callback_data="pay:wallet")
    b.button(text="◀ Back",               callback_data="menu:main")
    b.adjust(1)
    return b.as_markup()


def back_button(target: str = "menu:main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀ Back", callback_data=target)]]
    )


def admin_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📊 Stats",        callback_data="admin:stats")
    b.button(text="📢 Broadcast",    callback_data="admin:broadcast")
    b.button(text="👤 Lookup user",  callback_data="admin:lookup")
    b.button(text="🔒 Ban user",     callback_data="admin:ban")
    b.button(text="✅ Unban user",   callback_data="admin:unban")
    b.adjust(2, 2, 1)
    return b.as_markup()
