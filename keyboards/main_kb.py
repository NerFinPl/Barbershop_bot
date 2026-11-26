"""Главное меню и переходы между разделами.

Подписи кнопок держу здесь же: тянуть сюда messages.yml ради четырёх строк
не хочется, а когда всё переедет на app.texts - поменяю только константы.
"""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BTN_BOOK = "💈 Записаться"
BTN_RECORDS = "📋 Мои записи"
BTN_SERVICES = "✂️ Услуги"
BTN_MASTERS = "👤 Мастера"
BTN_ABOUT = "ℹ️ О нас"
BTN_HOME = "🏠 В меню"
BTN_BACK = "⬅️ Назад"


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_BOOK, callback_data="menu:book")],
            [InlineKeyboardButton(text=BTN_RECORDS, callback_data="menu:records")],
            [
                InlineKeyboardButton(text=BTN_SERVICES, callback_data="menu:services"),
                InlineKeyboardButton(text=BTN_MASTERS, callback_data="menu:masters"),
            ],
            [InlineKeyboardButton(text=BTN_ABOUT, callback_data="menu:about")],
        ]
    )


def back_to_menu() -> InlineKeyboardMarkup:
    """Одна кнопка домой - пригодится почти в каждом разделе."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=BTN_HOME, callback_data="menu:home")]]
    )


def info_section(section: str) -> InlineKeyboardMarkup:
    """Клавиатура под текстом раздела (services/masters/about).

    section приходит строкой из handlers/info.py. На сами кнопки он влияет
    только одним образом: не показываю ссылку на раздел, в котором мы уже сидим.
    """
    rows: list[list[InlineKeyboardButton]] = []

    sibling = {
        "services": (BTN_MASTERS, "menu:masters"),
        "masters": (BTN_SERVICES, "menu:services"),
    }.get(section)
    if sibling:
        rows.append([InlineKeyboardButton(text=sibling[0], callback_data=sibling[1])])

    rows.append([InlineKeyboardButton(text=BTN_BOOK, callback_data="menu:book")])
    rows.append([InlineKeyboardButton(text=BTN_HOME, callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
