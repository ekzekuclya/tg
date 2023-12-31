import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

import asyncio
import logging
from tg.utils import check_inactive_users


async def periodic_check_inactive_users():
    while True:
        await check_inactive_users()
        await asyncio.sleep(300)
        print("STARTED PERIODIC CHECK")


async def main():
    from aiogram.enums.parse_mode import ParseMode
    from aiogram.fsm.storage.memory import MemoryStorage
    from tg import config
    from tg.handlers import router as handlers_router
    from tg.channels import router as channels_router
    from aiogram import Bot, Dispatcher
    bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.MARKDOWN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_routers(handlers_router, channels_router)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print(f"An error occurred: {e}")
    asyncio.create_task(periodic_check_inactive_users())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())


