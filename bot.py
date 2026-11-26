"""Точка входа: поднимаем БД, подключаем роутеры, запускаем polling + напоминания."""
from __future__ import annotations

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from config import BOT_NAME, REMINDER
from db import get_storage
from handlers import booking, info, payment, records, start
from services.reminders import scheduler, start_scheduler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("barber")


async def main() -> None:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token or "замените" in token:
        logger.error("BOT_TOKEN не задан. Скопируйте .env.example → .env и впишите токен от @BotFather.")
        sys.exit(1)

    # инициализируем БД до старта polling, чтобы первый же хендлер не упал
    storage = get_storage()
    await storage.init()
    logger.info("База данных готова")

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # порядок имеет значение: booking первым - у него FSM-фильтры по состояниям
    dp.include_router(booking.router)
    dp.include_router(records.router)
    dp.include_router(payment.router)
    dp.include_router(info.router)
    dp.include_router(start.router)

    start_scheduler(bot)
    logger.info("Бот %s запущен. Напоминания: %s", BOT_NAME, "вкл" if REMINDER["enabled"] else "выкл")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Остановлено")
