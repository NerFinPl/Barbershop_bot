"""
⚙️ config.py - единственный файл, который нужно править при настройке бота.
   Здесь услуги, мастера, цены, оплата, напоминания, тексты кнопок и выбор БД.
   Секреты (BOT_TOKEN, ключи платёжных систем) - только в .env.
"""
from __future__ import annotations

from typing import Any

# ──────────────────────── 🪪 Основное ────────────────────────
BOT_NAME = "Barber & Co"
TIMEZONE = "Europe/Moscow"      # часовой пояс салона - важен для напоминаний
CURRENCY = "BYN"

SHOP: dict[str, Any] = {
    "name": "Barber & Co",
    "tagline": "Барбершоп, в который возвращаются",
    "address": "г. Минск, ул. Немига 12, 2 этаж",
    "phone": "+375 29 123-45-67",
    "work_hours": "Ежедневно · 10:00 - 21:00",
    "instagram": "https://instagram.com/barber.co",
    "map_url": "https://yandex.by/maps/",
    "about": (
        "🔹 <b>Barber &amp; Co</b> - 5 лет стрижём так, чтобы возвращались друзьями.\n"
        "🔹 Кофе, винил и никакой спешки - на всё про всё час.\n"
        "🔹 Работаем на American Crew и Reuzel, инструмент стерилизуем после каждого гостя.\n"
        "🔹 Мы в 3 минутах от метро, есть парковка."
    ),
}

# ──────────────────────── 💾 База данных ────────────────────────
DATABASE: dict[str, Any] = {
    "type": "sqlite",              # "sqlite" (по умолчанию) или "mysql"
    "sqlite_path": "barber.db",
    "mysql": {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "barber",
        "password": "barber",
        "database": "barber",
    },
}

# ──────────────────────── ✂️ Услуги ────────────────────────
# Цена привязана к услуге, а не к мастеру.
# Новая услуга = новый словарь ниже, код править не нужно.
SERVICES: dict[str, dict[str, Any]] = {
    "haircut": {
        "name": "Мужская стрижка",
        "emoji": "✂️",
        "price": 45,
        "duration": 45,
        "description": "Классика, фейд или что-то своё - обсуждаем и делаем под ваш стиль.",
    },
    "haircut_vip": {
        "name": "Стрижка + укладка",
        "emoji": "💈",
        "price": 60,
        "duration": 60,
        "description": "Стрижка с укладкой и стайлингом, чтобы вышли как с обложки.",
    },
    "beard": {
        "name": "Оформление бороды",
        "emoji": "🧔",
        "price": 30,
        "duration": 30,
        "description": "Контур, форма, горячее полотенце и масло в финале.",
    },
    "combo": {
        "name": "Стрижка + борода",
        "emoji": "🔥",
        "price": 65,
        "duration": 75,
        "description": "Полный образ за один визит. Наш самый популярный вариант.",
    },
    "shave": {
        "name": "Королевское бритьё",
        "emoji": "🪒",
        "price": 40,
        "duration": 45,
        "description": "Опасная бритва, пар, компрессы - ритуал, а не просто бритьё.",
    },
    "kids": {
        "name": "Детская стрижка",
        "emoji": "🧒",
        "price": 30,
        "duration": 30,
        "description": "До 12 лет. Мультики, шутки и никаких слёз.",
    },
    "camouflage": {
        "name": "Камуфляж седины",
        "emoji": "🎨",
        "price": 50,
        "duration": 60,
        "description": "Тонирование седых волос - естественно и мягко.",
    },
}

# ──────────────────────── 💈 Мастера ────────────────────────
# У каждого мастера свой набор услуг: "services" - список id из SERVICES выше.
MASTERS: dict[str, dict[str, Any]] = {
    "ivanov": {
        "name": "Иванов Иван",
        "emoji": "👨🦱",
        "title": "Топ-барбер",
        "experience": "8 лет",
        "description": "Фейды, классика, работа с бородой. Победитель Belarus Barber Battle 2023.",
        "services": ["haircut", "haircut_vip", "beard", "combo", "shave"],
    },
    "petrov": {
        "name": "Петров Артём",
        "emoji": "🧑🎤",
        "title": "Барбер-стилист",
        "experience": "5 лет",
        "description": "Любит эксперименты, текстурные стрижки и нестандартные формы.",
        "services": ["haircut", "beard", "combo", "camouflage", "kids"],
    },
    "sidorova": {
        "name": "Сидорова Мария",
        "emoji": "👩🎨",
        "title": "Барбер · детский мастер",
        "experience": "6 лет",
        "description": "Найдёт подход и к подростку, и к трёхлетке. Аккуратность на первом месте.",
        "services": ["haircut", "haircut_vip", "kids", "camouflage"],
    },
}

# ──────────────────────── 📅 Запись ────────────────────────
BOOKING: dict[str, Any] = {
    "days_ahead": 14,       # на сколько дней вперёд показываем даты
    "slot_step": 30,        # шаг сетки времени, минут
    "work_start": "10:00",
    "work_end": "20:30",
}

# Кнопка «Я опоздаю» - варианты задержки, минут
LATE_OPTIONS: list[int] = [5, 10, 15, 20]

# ──────────────────────── 🔔 Напоминания ────────────────────────
REMINDER: dict[str, Any] = {
    "enabled": True,
    "before_minutes": 120,      # за сколько минут до визита напоминать
}

# ──────────────────────── 💳 Оплата ────────────────────────
# Каждый провайдер включается/выключается здесь, ключи - в .env
PAYMENTS: dict[str, dict[str, Any]] = {
    "bepay":    {"enabled": True, "title": "BePaY 🇧🇾",   "currency": "BYN"},
    "yookassa": {"enabled": True, "title": "ЮKassa 🇷🇺",  "currency": "RUB"},
    "onsite":   {"enabled": True, "title": "На месте 💵"},
}

# ──────────────────────── ☎️ Поддержка ────────────────────────
SUPPORT: dict[str, Any] = {
    "manager": "@barber_support",
    "phone": "+375 29 123-45-67",
    "hours": "ежедневно 10:00 - 21:00",
}

# ──────────────────────── 🔤 Тексты кнопок ────────────────────────
BUTTONS: dict[str, str] = {
    "book": "📅 Записаться",
    "my_records": "🗓 Мои записи",
    "services": "✂️ Услуги и цены",
    "masters": "💈 Мастера",
    "support": "☎️ Поддержка",
    "about": "ℹ️ О нас",
}
