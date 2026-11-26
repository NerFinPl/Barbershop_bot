"""Уведомления админу/менеджеру (например, когда клиент предупредил об опоздании)."""
from __future__ import annotations

import os

from aiogram import Bot


async def notify_admin(bot: Bot, text: str) -> None:
    chat_id = os.getenv("ADMIN_CHAT_ID") or ""
    if not chat_id.strip():
        return
    try:
        await bot.send_message(int(chat_id), text)
    except Exception:
        # админ без прав / неверный ID - молча пропускаем
        pass
