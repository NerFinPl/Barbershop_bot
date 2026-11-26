"""Тексты и подписи кнопок из messages.yml.

Обращение максимально похоже на код: T.booking.ask_name, T.buttons.book.
Если в шаблоне есть подстановки - просто вызываем: T.menu.welcome(name="Аня").
Неизвестный ключ падает сразу (опечатку видно на первом же тесте), а вот
неизвестная подстановка остаётся как есть и не роняет сообщение.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent


class TextKeyError(KeyError):
    """Ключа нет в messages.yml - значит опечатка в коде."""


class _Safe(dict):
    def __missing__(self, key: str) -> str:  # не превращаем сообщение в None
        return "{" + key + "}"


class _Text(str):
    def __call__(self, **kwargs: Any) -> str:
        return str(self).format_map(_Safe(kwargs))


class _Node:
    __slots__ = ("_data", "_path")

    def __init__(self, data: dict[str, Any], path: str = "") -> None:
        self._data = data
        self._path = path

    def __getattr__(self, item: str) -> Any:
        if item.startswith("_"):
            raise AttributeError(item)
        if item not in self._data:
            raise TextKeyError(f"messages.yml: нет ключа '{self._path}{item}'")
        value = self._data[item]
        if isinstance(value, dict):
            return _Node(value, f"{self._path}{item}.")
        return _Text(str(value))

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def __contains__(self, item: str) -> bool:
        return item in self._data

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return getattr(self, item)
        except (AttributeError, TextKeyError):
            return default


class Texts(_Node):
    """Точка входа: T.booking.card(...), T.buttons.back."""

    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)


class _TSingleton:
    _instance: Texts | None = None

    def __getattr__(self, item: str) -> Any:
        if self._instance is None:
            path = BASE_DIR / "messages.yml"
            with path.open("r", encoding="utf-8") as fh:
                raw = yaml.safe_load(fh) or {}
            self._instance = Texts(raw)
        return getattr(self._instance, item)


T = _TSingleton()
