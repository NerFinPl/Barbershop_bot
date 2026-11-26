"""Клавиатуры раздела «Мои записи»: список, карточка, отмена, опоздание, перенос.

callback_data (сверял с handlers/records.py):
  rec:open:<id>        открыть карточку
  rec:cancel:<id>      переспросить про отмену
  rec:cancel_ok:<id>   отменить окончательно
  rec:late:<id>        выбор на сколько опоздаю
  rec:late_ok:<id>:<мин>
  mv:master:<id>  mv:date:<iso>  mv:time:<HH:MM>
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards._data import masters as _masters_map

MASTERS = _masters_map()

BTN_BACK = "⬅️ Назад"
BTN_HOME = "🏠 В меню"
BTN_CANCEL = "❌ Отменить запись"
BTN_LATE = "⏰ Я опоздаю"
BTN_MOVE = "🔄 Перенести"

LATE_MINUTES = (5, 10, 15, 20)
WEEKDAYS = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")


def _as_dict(row: Any) -> dict[str, Any]:
    """Записи приходят то объектом из storage, то обычной строкой из БД."""
    if hasattr(row, "to_dict"):
        return row.to_dict()
    if isinstance(row, dict):
        return row
    return dict(row)


def records_list_kb(rows: list[Any]) -> InlineKeyboardMarkup:
    """Список записей: одна кнопка на запись - по дате и времени ориентироваться проще."""
    keyboard: list[list[InlineKeyboardButton]] = []

    for row in rows:
        data = _as_dict(row)
        rec_id = data.get("id")
        if rec_id is None:
            continue
        label = " · ".join(
            part
            for part in (str(data.get("date_iso") or ""), str(data.get("time_str") or ""))
            if part
        ) or f"Запись #{rec_id}"
        keyboard.append(
            [InlineKeyboardButton(text=f"📅 {label}", callback_data=f"rec:open:{rec_id}")]
        )

    keyboard.append([InlineKeyboardButton(text=BTN_HOME, callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def record_card_kb(rec_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_MOVE, callback_data=f"rec:move:{rec_id}")],
            [InlineKeyboardButton(text=BTN_LATE, callback_data=f"rec:late:{rec_id}")],
            [InlineKeyboardButton(text=BTN_CANCEL, callback_data=f"rec:cancel:{rec_id}")],
            [InlineKeyboardButton(text=BTN_BACK, callback_data="menu:records")],
        ]
    )


def cancel_confirm_kb(rec_id: int) -> InlineKeyboardMarkup:
    """Переспрашиваем: отмену записи назад не открутишь."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Да, отменить", callback_data=f"rec:cancel_ok:{rec_id}")],
            [InlineKeyboardButton(text="Оставить как есть", callback_data=f"rec:open:{rec_id}")],
        ]
    )


def late_kb(rec_id: int) -> InlineKeyboardMarkup:
    """На сколько опоздаю. Минуты в callback - чтобы хендлер не ходил в базу за мелочью."""
    keyboard: list[list[InlineKeyboardButton]] = []
    chunk: list[InlineKeyboardButton] = []
    for minutes in LATE_MINUTES:
        chunk.append(
            InlineKeyboardButton(
                text=f"+{minutes} мин",
                callback_data=f"rec:late_ok:{rec_id}:{minutes}",
            )
        )
    keyboard.append(chunk)
    keyboard.append([InlineKeyboardButton(text=BTN_BACK, callback_data=f"rec:open:{rec_id}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def move_master_kb(master_id: str | None = None) -> InlineKeyboardMarkup:
    """Перенос, шаг 1 - к кому. Текущего мастера не показываю, перенос к нему бессмыслен."""
    keyboard: list[list[InlineKeyboardButton]] = []
    for current_id, master in MASTERS.items():
        if current_id == master_id:
            continue
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{master.get('emoji', '💈')} {master.get('name', current_id)}",
                    callback_data=f"mv:master:{current_id}",
                )
            ]
        )
    keyboard.append([InlineKeyboardButton(text=BTN_BACK, callback_data="menu:records")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def move_dates_kb(*args, **kwargs) -> InlineKeyboardMarkup:
    """Перенос, шаг 2 - на какой день. Две недели вперёд, как и при записи.

    Сигнатуру хендлера целиком не видел, поэтому лишние позиционные аргументы
    просто игнорирую - на клавиатуру они всё равно не влияют.
    """
    days_ahead = int(kwargs.get("days_ahead") or 14)
    start = date.today()

    keyboard: list[list[InlineKeyboardButton]] = []
    chunk: list[InlineKeyboardButton] = []
    for offset in range(days_ahead):
        day = start + timedelta(days=offset)
        chunk.append(
            InlineKeyboardButton(
                text=f"{WEEKDAYS[day.weekday()]} {day.strftime('%d.%m')}",
                callback_data=f"mv:date:{day.isoformat()}",
            )
        )
        if len(chunk) == 3:
            keyboard.append(chunk)
            chunk = []
    if chunk:
        keyboard.append(chunk)

    keyboard.append([InlineKeyboardButton(text=BTN_BACK, callback_data="menu:records")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def move_times_kb(*args, **kwargs) -> InlineKeyboardMarkup:
    """Перенос, шаг 3 - время. Слоты всегда приходят снаружи, из services.free_slots."""
    slots: list[str] = []
    for arg in args:
        if isinstance(arg, (list, tuple, set)):
            slots = [str(item) for item in arg]
    slots = [str(item) for item in (kwargs.get("slots") or slots)]

    keyboard: list[list[InlineKeyboardButton]] = []
    chunk: list[InlineKeyboardButton] = []
    for slot in slots:
        chunk.append(InlineKeyboardButton(text=slot, callback_data=f"mv:time:{slot}"))
        if len(chunk) == 4:
            keyboard.append(chunk)
            chunk = []
    if chunk:
        keyboard.append(chunk)

    keyboard.append([InlineKeyboardButton(text=BTN_BACK, callback_data="menu:records")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
