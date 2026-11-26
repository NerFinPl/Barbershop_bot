"""Услуги, мастера, о нас, поддержка."""
from __future__ import annotations

import os

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.main_kb import info_section
from messages import M
from services.notify import notify_admin

router = Router(name="info")


@router.callback_query(F.data == "menu:services")
async def show_services(call: CallbackQuery) -> None:
    await call.message.edit_text(M.services_list(), reply_markup=info_section("services"))
    await call.answer()


@router.callback_query(F.data == "menu:masters")
async def show_masters(call: CallbackQuery) -> None:
    await call.message.edit_text(M.masters_list(), reply_markup=info_section("masters"))
    await call.answer()


@router.callback_query(F.data == "menu:about")
async def show_about(call: CallbackQuery) -> None:
    await call.message.edit_text(M.about(), reply_markup=info_section("about"))
    await call.answer()


@router.callback_query(F.data == "menu:support")
async def show_support(call: CallbackQuery) -> None:
    await call.message.edit_text(M.support(), reply_markup=info_section("support"))
    await call.answer()
