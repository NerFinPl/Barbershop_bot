"""Выбор способа оплаты после подтверждения записи.

Онлайн-провайдеров беру из config.PAYMENTS: если провайдер выключен или не
настроен, кнопку не показываю вообще, чтобы не вести клиента в тупик.
"""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BTN_HOME = "🏠 В меню"
BTN_ONSITE = "🏠 Оплата на месте"

LABELS = {
    "bepay": "💳 BePaY",
    "yookassa": "💳 ЮKassa",
}


def _online_providers() -> list[tuple[str, str]]:
    # Список провайдеров пока живёт только в старом config.py, но шим уже есть -
    # когда переедет в yml, править надо будет одну функцию в _data.
    from keyboards._data import payments as _payments_map

    PAYMENTS = _payments_map()

    providers: list[tuple[str, str]] = []
    for name, options in (PAYMENTS or {}).items():
        options = options or {}
        if not options.get("enabled", True):
            continue
        providers.append((name, options.get("title") or LABELS.get(name, name)))
    return providers


def payment_kb(rec_id: int, price: int | None = None) -> InlineKeyboardMarkup:
    """price пока не нужен - сумма уже записана в самой записи. Параметр оставил
    на случай, если хендлер его передаёт."""
    keyboard: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=BTN_ONSITE, callback_data=f"pay:onsite:{rec_id}")]
    ]

    for name, label in _online_providers():
        keyboard.append([InlineKeyboardButton(text=label, callback_data=f"pay:{name}:{rec_id}")])

    keyboard.append([InlineKeyboardButton(text=BTN_HOME, callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
