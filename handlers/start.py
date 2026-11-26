"""/start и главное меню."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from keyboards.main_kb import main_menu
from messages import M

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    name = message.from_user.first_name or "друг"
    await message.answer(M.welcome(name), reply_markup=main_menu())


@router.callback_query(F.data == "menu:home")
async def back_home(call: CallbackQuery) -> None:
    await call.message.edit_text(M.menu_hint, reply_markup=main_menu())
    await call.answer()
