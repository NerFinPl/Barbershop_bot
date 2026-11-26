"""Оплата после подтверждения записи: онлайн (BePaY / ЮKassa) или на месте."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from config import CURRENCY, PAYMENTS
from db import get_storage
from keyboards.main_kb import main_menu
from messages import M
from payments import get_provider

router = Router(name="payment")


@router.callback_query(F.data.startswith("pay:onsite:"))
async def pay_onsite(call: CallbackQuery) -> None:
    rec_id = int(call.data.split(":")[2])
    storage = get_storage()
    await storage.update_appointment(rec_id, payment="onsite")
    await call.message.edit_text(M.pay_onsite, reply_markup=main_menu())
    await call.answer()


@router.callback_query(F.data.startswith("pay:bepay:"))
@router.callback_query(F.data.startswith("pay:yookassa:"))
async def pay_online(call: CallbackQuery) -> None:
    _, provider_name, rec_id_s = call.data.split(":")
    rec_id = int(rec_id_s)
    storage = get_storage()
    rec = await storage.get_appointment(rec_id)
    if not rec:
        await call.answer(M.not_found, show_alert=True)
        return

    provider = get_provider(provider_name)
    if provider is None:
        await call.answer(M.pay_failed, show_alert=True)
        return

    currency = PAYMENTS[provider_name].get("currency", CURRENCY)
    result = await provider.create_payment(
        amount=rec.price,
        description=f"Запись #{rec.id}: {rec.service_id}",
        payload=f"appt:{rec.id}",
    )
    if not result.ok or not result.pay_url:
        await call.answer(M.pay_failed, show_alert=True)
        return

    await storage.update_appointment(rec_id, payment="online", payment_id=result.payment_id)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Перейти к оплате", url=result.pay_url)],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:home")],
        ]
    )
    await call.message.edit_text(M.pay_link(rec.price, currency), reply_markup=kb)
    await call.answer()
