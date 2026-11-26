"""Валидаторы имени и телефона - простые, но отсекают явный мусор."""
from __future__ import annotations

import re


NAME_RE = re.compile(r"^[А-Яа-яЁёA-Za-z\s\-']{2,40}$")
# Допускаем +, пробелы, дефисы, скобки и 10-15 цифр
PHONE_DIGITS = re.compile(r"\D")


def is_valid_name(text: str) -> bool:
    text = text.strip()
    return bool(NAME_RE.match(text)) and " " not in text[:1]


def normalize_phone(text: str) -> str | None:
    """Возвращает '+375291234567' либо None, если номер явно невалиден."""
    digits = PHONE_DIGITS.sub("", text)
    if len(digits) < 10 or len(digits) > 15:
        return None
    return "+" + digits if not digits.startswith("+") else digits
