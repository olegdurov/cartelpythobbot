"""
main.py — AlphaBot entry point
"""
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from bot.handlers import onboarding, menu, billing, referral, admin
from bot.middlewares.db import DatabaseMiddleware
from bot.middlewares.subscription import SubscriptionMiddleware

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    bot = Bot(
        token=os.environ["BOT_TOKEN"],
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    storage = RedisStorage.from_url(os.environ["REDIS_URL"])
    dp = Dispatcher(storage=storage)

    # Middlewares
    dp.update.middleware(DatabaseMiddleware())
    dp.update.middleware(SubscriptionMiddleware())

    # Routers
    dp.include_router(onboarding.router)
    dp.include_router(menu.router)
    dp.include_router(billing.router)
    dp.include_router(referral.router)
    dp.include_router(admin.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
