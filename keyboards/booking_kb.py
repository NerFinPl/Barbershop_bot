"""Клавиатуры шагов записи: мастер, услуга, дата, время, телефон, подтверждение.

callback_data повторяет то, что уже ловят в handlers/booking.py:
  bk:m:<master_id>   bk:s:<master_id>:<service_id>   bk:d:<iso>   bk:t:<HH:MM>
  bk:confirm   bk:promo   bk:back:<шаг>
"""
from __future__ import annotations

from datetime import date, timedelta

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# Прямой импорт из config.py убрал: справочники теперь берём через keyboards._data,
# она читает и новый config.yml, и старый config.py. Когда старый конфиг выпилим,
# этот модуль трогать уже не придётся.
from keyboards._data import masters as _masters_map, services as _services_map

MASTERS = _masters_map()
SERVICES = _services_map()

BTN_BACK = "⬅️ Назад"
BTN_HOME = "🏠 В меню"
BTN_CONFIRM = "✅ Подтвердить"
BTN_PROMO = "🎁 Промокод"

DAYS_AHEAD = 14
WEEKDAYS = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")


def _master(master_id: str) -> dict:
    return MASTERS.get(master_id) or {}


def _service(service_id: str) -> dict:
    return SERVICES.get(service_id) or {}


def masters_kb() -> InlineKeyboardMarkup:
    """Шаг 1. По одному мастеру в строку - имена длинные, иначе не влезают."""
    rows: list[list[InlineKeyboardButton]] = []
    for master_id, master in MASTERS.items():
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{master.get('emoji', '💈')} {master.get('name', master_id)}",
                    callback_data=f"bk:m:{master_id}",
                )
            ]
        )

    rows.append([InlineKeyboardButton(text=BTN_HOME, callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def services_kb(master_id: str) -> InlineKeyboardMarkup:
    """Шаг 2. Только те услуги, которые мастер реально делает."""
    master = _master(master_id)
    service_ids = master.get("services") or list(SERVICES.keys())

    rows: list[list[InlineKeyboardButton]] = []
    for service_id in service_ids:
        service = _service(service_id)
        name = service.get("name", service_id)
        price = service.get("price")
        label = f"{service.get('emoji', '✂️')} {name}"
        if price is not None:
            label += f" · {price} BYN"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"bk:s:{master_id}:{service_id}")]
        )

    # В handlers/booking.py обработчик висит ровно на "bk:back:masters" -
    # поэтому во множественном числе, хотя возвращает к одному мастеру.
    rows.append([InlineKeyboardButton(text=BTN_BACK, callback_data="bk:back:masters")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _day_label(day: date) -> str:
    return f"{WEEKDAYS[day.weekday()]} {day.strftime('%d.%m')}"


def dates_kb(*args, **kwargs) -> InlineKeyboardMarkup:
    """Шаг 3, выбор дня. Ближайшие две недели по три дня в ряд.

    Свободные окна тут не считаю: это работа services.free_slots, а клавиатура
    должна оставаться дешёвой. Пустой день просто отсеется на шаге времени.
    Лишние аргументы игнорирую - хендлер может передавать master_id/service_id.
    """
    days_ahead = int(kwargs.get("days_ahead") or DAYS_AHEAD)
    today = date.today()

    rows: list[list[InlineKeyboardButton]] = []
    chunk: list[InlineKeyboardButton] = []
    for offset in range(days_ahead):
        day = today + timedelta(days=offset)
        chunk.append(
            InlineKeyboardButton(text=_day_label(day), callback_data=f"bk:d:{day.isoformat()}")
        )
        if len(chunk) == 3:
            rows.append(chunk)
            chunk = []
    if chunk:
        rows.append(chunk)

    rows.append([InlineKeyboardButton(text=BTN_BACK, callback_data="bk:back:service")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def times_kb(*args, **kwargs) -> InlineKeyboardMarkup:
    """Шаг 3, выбор времени.

    Точную сигнатуру в booking.py я не видел целиком, поэтому вытаскиваю список
    слотов и дату из позиционных аргументов - так модуль не развалится, если
    хендлер передаст на один параметр больше или меньше.
    """
    slots: list[str] = []
    date_iso = ""

    for arg in args:
        if isinstance(arg, (list, tuple, set)):
            slots = [str(item) for item in arg]
        elif isinstance(arg, str) and len(arg) == 10 and arg[4] == "-":
            date_iso = arg

    slots = [str(item) for item in (kwargs.get("slots") or slots)]
    date_iso = kwargs.get("date_iso") or date_iso

    rows: list[list[InlineKeyboardButton]] = []
    chunk: list[InlineKeyboardButton] = []
    for slot in slots:
        chunk.append(InlineKeyboardButton(text=slot, callback_data=f"bk:t:{slot}"))
        if len(chunk) == 4:
            rows.append(chunk)
            chunk = []
    if chunk:
        rows.append(chunk)

    # Отдельного обработчика на возврат к датам в booking.py нет - веду на
    # список мастеров, откуда шаг начинается заново и точно не зависнет.
    rows.append([InlineKeyboardButton(text=BTN_BACK, callback_data="bk:back:masters")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def phone_kb() -> ReplyKeyboardMarkup:
    """Шаг 4. Единственная reply-клавиатура во всём флоу - из-за request_contact."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить мой номер", request_contact=True)],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def confirm_flow(*args, **kwargs) -> InlineKeyboardMarkup:
    """Шаг 5. Подтверждение записи.

    Хендлер зовёт confirm_flow(message.from_user.id) - то есть первым аргументом
    приходит id пользователя, а вовсе не шаг. Раньше я подставлял его в callback
    и получал несуществующий bk:back:12345, то есть мёртвую кнопку. Теперь любые
    позиционные аргументы игнорирую: возврат всегда на выбор мастера, там есть
    живой обработчик bk:back:masters.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_CONFIRM, callback_data="bk:confirm")],
            [InlineKeyboardButton(text=BTN_PROMO, callback_data="bk:promo")],
            [InlineKeyboardButton(text=BTN_BACK, callback_data="bk:back:masters")],
        ]
    )
