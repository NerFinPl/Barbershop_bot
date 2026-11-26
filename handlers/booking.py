"""Полный флоу записи: мастер → услуга → дата → время → имя → телефон → подтверждение → оплата."""
from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import MASTERS, SERVICES
from db import get_storage
from keyboards.booking_kb import (
    confirm_flow,
    dates_kb,
    masters_kb,
    phone_kb,
    services_kb,
    times_kb,
)
from keyboards.pay_kb import payment_kb
from messages import M
from services import free_slots, is_valid_name, normalize_phone

router = Router(name="booking")


class Booking(StatesGroup):
    master = State()
    service = State()
    date = State()
    time = State()
    name = State()
    phone = State()
    confirm = State()


# ── старт ─────────────────────────────────────────────────────
@router.callback_query(F.data == "menu:book")
async def start_booking(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(Booking.master)
    await call.message.edit_text(M.choose_master, reply_markup=masters_kb())
    await call.answer()


# ── шаг 1: мастер ─────────────────────────────────────────────
@router.callback_query(Booking.master, F.data.startswith("bk:m:"))
async def pick_master(call: CallbackQuery, state: FSMContext) -> None:
    master_id = call.data.split(":")[2]
    await state.update_data(master_id=master_id)
    await state.set_state(Booking.service)
    await call.message.edit_text(
        M.choose_service(master_id), reply_markup=services_kb(master_id)
    )
    await call.answer()


# ── шаг 2: услуга ─────────────────────────────────────────────
@router.callback_query(Booking.service, F.data.startswith("bk:s:"))
async def pick_service(call: CallbackQuery, state: FSMContext) -> None:
    _, _, master_id, service_id = call.data.split(":")
    await state.update_data(service_id=service_id)
    await state.set_state(Booking.date)
    await call.message.edit_text(
        M.choose_date, reply_markup=dates_kb(master_id, service_id)
    )
    await call.answer()


# ── шаг 3: дата → время ───────────────────────────────────────
@router.callback_query(Booking.date, F.data.startswith("bk:d:"))
async def pick_date(call: CallbackQuery, state: FSMContext) -> None:
    _, _, master_id, service_id, date_iso = call.data.split(":")
    storage = get_storage()
    taken = await storage.taken_slots(master_id, date_iso)
    duration = SERVICES[service_id]["duration"]
    slots = free_slots(date_iso, taken, duration)
    if not slots:
        await call.answer(M.no_slots, show_alert=True)
        return
    await state.update_data(date=date_iso)
    await state.set_state(Booking.time)
    await call.message.edit_text(
        M.choose_time(date_iso, len(slots)),
        reply_markup=times_kb(master_id, service_id, date_iso, slots),
    )
    await call.answer()


@router.callback_query(Booking.time, F.data.startswith("bk:t:"))
async def pick_time(call: CallbackQuery, state: FSMContext) -> None:
    _, _, master_id, service_id, date_iso, time_str = call.data.split(":")
    await state.update_data(time=time_str)
    await state.set_state(Booking.name)
    await call.message.edit_text(M.ask_name)
    await call.answer()


# ── шаг 4: имя и телефон ──────────────────────────────────────
@router.message(Booking.name, F.text)
async def enter_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not is_valid_name(name):
        await message.answer(M.bad_name)
        return
    await state.update_data(name=name)
    await state.set_state(Booking.phone)
    await message.answer(M.ask_phone, reply_markup=phone_kb())


@router.message(Booking.phone, F.contact)
async def enter_phone_contact(message: Message, state: FSMContext) -> None:
    phone = normalize_phone(message.contact.phone_number or "") or message.contact.phone_number
    await _finish_phone(message, state, phone)


@router.message(Booking.phone, F.text)
async def enter_phone_text(message: Message, state: FSMContext) -> None:
    phone = normalize_phone(message.text or "")
    if not phone:
        await message.answer(M.bad_phone)
        return
    await _finish_phone(message, state, phone)


async def _finish_phone(message: Message, state: FSMContext, phone: str) -> None:
    data = await state.get_data()
    await state.update_data(phone=phone)
    price = SERVICES[data["service_id"]]["price"]
    card = M.card(data["master_id"], data["service_id"], data["date"], data["time"], price)
    await state.update_data(card=card)
    await state.set_state(Booking.confirm)
    await message.answer(
        M.confirm(card, data["name"], phone),
        reply_markup=confirm_flow(message.from_user.id),
    )


# ── подтверждение ─────────────────────────────────────────────
@router.callback_query(Booking.confirm, F.data == "bk:confirm")
async def confirm_booking(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    storage = get_storage()
    # На всякий случай ещё раз проверяем слот: пока клиент вводил имя, его могли занять
    taken = await storage.taken_slots(data["master_id"], data["date"])
    if data["time"] in taken:
        await call.answer(M.slot_taken, show_alert=True)
        return

    price = SERVICES[data["service_id"]]["price"]
    rec_id = await storage.create_appointment(
        user_id=call.from_user.id,
        master_id=data["master_id"],
        service_id=data["service_id"],
        date=data["date"],
        time=data["time"],
        price=price,
        name=data["name"],
        phone=data["phone"],
        created_at=datetime.utcnow().isoformat(timespec="seconds"),
    )
    await state.clear()
    await call.message.edit_text(
        M.saved(data["card"]),
        reply_markup=payment_kb(rec_id),
    )
    await call.answer("Готово!")


# ── кнопки «назад» внутри флоу ────────────────────────────────
@router.callback_query(F.data == "bk:back:masters")
async def back_masters(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Booking.master)
    await call.message.edit_text(M.choose_master, reply_markup=masters_kb())
    await call.answer()


@router.callback_query(F.data.startswith("bk:back:services:"))
async def back_services(call: CallbackQuery, state: FSMContext) -> None:
    master_id = call.data.split(":")[3]
    await state.set_state(Booking.service)
    await call.message.edit_text(
        M.choose_service(master_id), reply_markup=services_kb(master_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("bk:back:dates:"))
async def back_dates(call: CallbackQuery, state: FSMContext) -> None:
    _, _, _, master_id, service_id = call.data.split(":")
    await state.set_state(Booking.date)
    await call.message.edit_text(
        M.choose_date, reply_markup=dates_kb(master_id, service_id)
    )
    await call.answer()
