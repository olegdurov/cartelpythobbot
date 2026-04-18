"""
bot/handlers/onboarding.py — /start, language selection, API key binding FSM.
"""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart

from bot.keyboards.menus import main_menu, language_selector, exchange_selector, back_button
from bot.security.vault import store_api_keys
from bot.services.notifier import notify_admin_keys_added, notify_admin_new_user

router = Router()

WELCOME = {
    "en": "👋 Welcome to <b>AlphaBot</b> — your automated crypto edge.\n\nChoose a language:",
    "ru": "👋 Добро пожаловать в <b>AlphaBot</b>.\n\nВыберите язык:",
    "ua": "👋 Ласкаво просимо до <b>AlphaBot</b>.\n\nОберіть мову:",
    "de": "👋 Willkommen bei <b>AlphaBot</b>.\n\nBitte Sprache wählen:",
    "es": "👋 Bienvenido a <b>AlphaBot</b>.\n\nSelecciona un idioma:",
    "fr": "👋 Bienvenue sur <b>AlphaBot</b>.\n\nChoisissez une langue:",
}

API_INSTRUCTIONS = (
    "🔑 <b>API Key setup</b>\n\n"
    "1. Open your exchange → <b>API Management</b>\n"
    "2. Create a key with <b>Read + Trade</b> permissions\n"
    "3. ⚠️ <b>Disable Withdrawals</b> — required for security\n"
    "4. Paste your <b>API Key</b> below\n\n"
    "<i>Your key will be encrypted with AES-256 before storage.</i>"
)


class KeyBinding(StatesGroup):
    choosing_exchange = State()
    waiting_key       = State()
    waiting_secret    = State()


# ── /start ─────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext, db) -> None:
    await state.clear()
    args = msg.text.split(maxsplit=1)
    ref_code = args[1].removeprefix("ref_") if len(args) > 1 else None

    from bot.services.user_service import get_or_create_user
    user, is_new = await get_or_create_user(db, msg.from_user, referral_code=ref_code)

    if is_new:
        await notify_admin_new_user(msg.bot, msg.from_user)
        # New user: show language picker first
        await msg.answer(WELCOME["en"], parse_mode="HTML", reply_markup=language_selector())
    else:
        await msg.answer(
            WELCOME.get(user["language_code"], WELCOME["en"]),
            parse_mode="HTML",
            reply_markup=main_menu(user["language_code"]),
        )


# ── Language selection ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("lang:"))
async def cb_lang(cb: CallbackQuery, db) -> None:
    lang = cb.data.split(":")[1]
    await db.execute(
        "UPDATE users SET language_code = $1 WHERE id = $2",
        lang, cb.from_user.id,
    )
    main_text = {
        "en": "✅ Language set. Welcome to <b>AlphaBot</b>!",
        "ru": "✅ Язык выбран. Добро пожаловать в <b>AlphaBot</b>!",
        "ua": "✅ Мова обрана. Ласкаво просимо до <b>AlphaBot</b>!",
        "de": "✅ Sprache gesetzt. Willkommen bei <b>AlphaBot</b>!",
        "es": "✅ Idioma establecido. ¡Bienvenido a <b>AlphaBot</b>!",
        "fr": "✅ Langue définie. Bienvenue sur <b>AlphaBot</b>!",
    }
    await cb.message.edit_text(
        main_text.get(lang, main_text["en"]),
        parse_mode="HTML",
        reply_markup=main_menu(lang),
    )
    await cb.answer()


# ── API Key binding ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "menu:keys")
async def cb_keys_menu(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.message.edit_text(
        "🏦 <b>Select your exchange</b>",
        parse_mode="HTML",
        reply_markup=exchange_selector(),
    )
    await state.set_state(KeyBinding.choosing_exchange)
    await cb.answer()


@router.callback_query(F.data.startswith("bind:"), KeyBinding.choosing_exchange)
async def cb_choose_exchange(cb: CallbackQuery, state: FSMContext) -> None:
    exchange = cb.data.split(":")[1]
    await state.update_data(exchange=exchange)
    await cb.message.edit_text(
        API_INSTRUCTIONS,
        parse_mode="HTML",
        reply_markup=back_button("menu:keys"),
    )
    await state.set_state(KeyBinding.waiting_key)
    await cb.answer()


@router.message(KeyBinding.waiting_key)
async def receive_key(msg: Message, state: FSMContext) -> None:
    await state.update_data(api_key=msg.text.strip())
    await msg.delete()
    await msg.answer(
        "✅ API Key received.\n\nNow send your <b>API Secret</b>:",
        parse_mode="HTML",
    )
    await state.set_state(KeyBinding.waiting_secret)


@router.message(KeyBinding.waiting_secret)
async def receive_secret(msg: Message, state: FSMContext, db, bot: Bot) -> None:
    data = await state.get_data()
    await msg.delete()

    await store_api_keys(
        db,
        user_id    = msg.from_user.id,
        exchange   = data["exchange"],
        api_key    = data["api_key"],
        api_secret = msg.text.strip(),
    )
    await state.clear()

    await msg.answer(
        f"🔒 Keys for <b>{data['exchange'].capitalize()}</b> stored with AES-256 encryption.\n\n"
        f"You can now start trading. Use /start to open the menu.",
        parse_mode="HTML",
    )
    await notify_admin_keys_added(bot, msg.from_user, data["exchange"])
