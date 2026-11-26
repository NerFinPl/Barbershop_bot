"""Мелкие помощники: форматирование дат, цен и текстовых блоков."""
from __future__ import annotations

from datetime import date

MONTHS = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]
WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


def human_date(iso: str) -> str:
    """'2024-06-03' -> '3 июня (пн)'."""
    d = date.fromisoformat(iso)
    return f"{d.day} {MONTHS[d.month - 1]} ({WEEKDAYS[d.weekday()]})"


def short_date(iso: str) -> str:
    """'2024-06-03' -> '03.06' - для компактных кнопок."""
    d = date.fromisoformat(iso)
    return f"{d.day:02d}.{d.month:02d}"


def money(amount: int | float, currency: str = "BYN") -> str:
    """45 -> '45 BYN'."""
    return f"{amount:g} {currency}"
