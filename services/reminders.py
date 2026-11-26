"""Планировщик напоминаний. Раз в минуту смотрим в БД, кому пора писать."""
from __future__ import annotations

from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import REMINDER, TIMEZONE
from db import get_storage
from messages import M

scheduler = AsyncIOScheduler(timezone=TIMEZONE)


async def check_reminders(bot: Bot) -> None:
    storage = get_storage()
    now = datetime.now()
    # Окно: сейчас и чуть дальше - чтобы захватить те, что попадут в нужный интервал
    window_from = (now + timedelta(minutes=REMINDER["before_minutes"])).strftime("%Y-%m-%d %H:%M")
    window_to = (now + timedelta(minutes=REMINDER["before_minutes"] + 1)).strftime("%Y-%m-%d %H:%M")
    try:
        due = await storage.due_reminders(window_from, window_to)
    except Exception:  # БД может ещё не подняться в самый первый тик
        return
    for appt in due:
        try:
            await bot.send_message(appt.user_id, M.reminder(appt.to_dict()))
            await storage.mark_reminded(appt.id)
        except Exception:
            # пользователь заблокировал бота или чат удалён - не падаем
            await storage.mark_reminded(appt.id)


def start_scheduler(bot: Bot) -> None:
    if not REMINDER["enabled"]:
        return
    # Интервал - раз в минуту: точности хватает.
    scheduler.add_job(
        check_reminders, "interval", minutes=1, args=[bot], id="reminders", replace_existing=True
    )
    scheduler.start()
