"""«Мои записи»: список, карточка, отмена, «я опоздаю», перенос."""
from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from config import CURRENCY, MASTERS, SERVICES
from db import get_storage
from keyboards.main_kb import main_menu
from keyboards.records_kb import (
    cancel_confirm_kb,
    late_kb,
    move_dates_kb,
    move_master_kb,
    move_times_kb,
    record_card_kb,
    records_list_kb,
)
from messages import M
from services import free_slots, notify_admin
from services.utils import human_date

router = Router(name="records")


# ── список ────────────────────────────────────────────────────
@router.callback_query(F.data == "menu:records")
async def list_records(call: CallbackQuery) -> None:
    storage = get_storage()
    rows = await storage.user_appointments(call.from_user.id)
    if not rows:
        await call.message.edit_text(M.no_records, reply_markup=main_menu())
        await call.answer()
        return
    await call.message.edit_text(
        M.my_records([r.to_dict() for r in rows]),
        reply_markup=records_list_kb(rows),
    )
    await call.answer()


# ── карточка ──────────────────────────────────────────────────
@router.callback_query(F.data.startswith("rec:open:"))
async def open_record(call: CallbackQuery) -> None:
    rec_id = int(call.data.split(":")[2])
    storage = get_storage()
    rec = await storage.get_appointment(rec_id)
    if not rec or rec.status != "active":
        await call.answer(M.not_found, show_alert=True)
        return
    await call.message.edit_text(
        M.record_card(rec.to_dict()),
        reply_markup=record_card_kb(rec_id),
    )
    await call.answer()


# ── отмена ────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("rec:cancel:"))
async def cancel_ask(call: CallbackQuery) -> None:
    rec_id = int(call.data.split(":")[2])
    await call.message.edit_text(M.cancel_ask, reply_markup=cancel_confirm_kb(rec_id))
    await call.answer()


@router.callback_query(F.data.startswith("rec:do_cancel:"))
async def cancel_do(call: CallbackQuery) -> None:
    rec_id = int(call.data.split(":")[2])
    storage = get_storage()
    await storage.update_appointment(rec_id, status="cancelled")
    rec = await storage.get_appointment(rec_id)
    await call.message.edit_text(M.cancelled, reply_markup=main_menu())
    await call.answer()
    if rec:
        await notify_admin(call.bot, f"❌ Отмена записи #{rec.id} ({rec.name}, {rec.phone})")


# ── «я опоздаю» ───────────────────────────────────────────────
@router.callback_query(F.data.startswith("rec:late:"))
async def late_ask(call: CallbackQuery) -> None:
    rec_id = int(call.data.split(":")[2])
    await call.message.edit_text(M.late_ask(), reply_markup=late_kb(rec_id))
    await call.answer()


@router.callback_query(F.data.startswith("rec:do_late:"))
async def late_do(call: CallbackQuery) -> None:
    _, _, rec_id_s, minutes_s = call.data.split(":")
    rec_id, minutes = int(rec_id_s), int(minutes_s)
    storage = get_storage()
    await storage.update_appointment(rec_id, late_minutes=minutes)
    rec = await storage.get_appointment(rec_id)
    await call.message.edit_text(M.late_done(minutes), reply_markup=main_menu())
    await call.answer()
    if rec:
        await notify_admin(
            call.bot,
            f"⏰ {rec.name} опоздает на {minutes} мин. "
            f"Запись #{rec.id}: {rec.time} к {rec.master_id}, тел. {rec.phone}",
        )


# ── перенос: мастер → дата → время ────────────────────────────
@router.callback_query(F.data.startswith("rec:move:"))
async def move_start(call: CallbackQuery) -> None:
    rec_id = int(call.data.split(":")[2])
    await call.message.edit_text(M.move_master, reply_markup=move_master_kb(rec_id))
    await call.answer()


@router.callback_query(F.data.startswith("rec:mv_m:"))
async def move_pick_master(call: CallbackQuery) -> None:
    _, _, rec_id_s, master_id = call.data.split(":")
    rec_id = int(rec_id_s)
    await call.message.edit_text(
        M.move_date, reply_markup=move_dates_kb(rec_id, master_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("rec:mv_d:"))
async def move_pick_date(call: CallbackQuery) -> None:
    _, _, rec_id_s, master_id, date_iso = call.data.split(":")
    rec_id = int(rec_id_s)
    storage = get_storage()
    rec = await storage.get_appointment(rec_id)
    duration = SERVICES[rec.service_id]["duration"] if rec else 30
    taken = await storage.taken_slots(master_id, date_iso)
    slots = free_slots(date_iso, taken, duration)
    if not slots:
        await call.answer(M.no_slots, show_alert=True)
        return
    await call.message.edit_text(
        M.move_time(date_iso),
        reply_markup=move_times_kb(rec_id, master_id, date_iso, slots),
    )
    await call.answer()


@router.callback_query(F.data.startswith("rec:mv_t:"))
async def move_pick_time(call: CallbackQuery) -> None:
    _, _, rec_id_s, master_id, date_iso, time_str = call.data.split(":")
    rec_id = int(rec_id_s)
    storage = get_storage()
    rec = await storage.get_appointment(rec_id)
    if not rec:
        await call.answer(M.not_found, show_alert=True)
        return

    # слот могли занять за время, пока пользователь кликал
    taken = await storage.taken_slots(master_id, date_iso)
    if time_str in taken:
        await call.answer(M.slot_taken, show_alert=True)
        return

    await storage.update_appointment(
        rec_id, master_id=master_id, date=date_iso, time=time_str
    )
    rec = await storage.get_appointment(rec_id)
    await call.message.edit_text(
        M.moved(M.record_card(rec.to_dict())), reply_markup=record_card_kb(rec_id)
    )
    await call.answer("Перенесено")
