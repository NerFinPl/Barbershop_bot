"""Слой доступа к данным. Снаружи работаем только через get_storage()."""
from __future__ import annotations

from config import DATABASE

from .base import Appointment, Storage

_storage: Storage | None = None


def get_storage() -> Storage:
    """Ленивая инициализация конкретной реализации БД по config.DATABASE['type']."""
    global _storage
    if _storage is not None:
        return _storage

    db_type = (DATABASE.get("type") or "sqlite").lower()
    if db_type == "mysql":
        from .mysql_storage import MySQLStorage

        _storage = MySQLStorage(DATABASE["mysql"])
    else:
        from .sqlite_storage import SQLiteStorage

        _storage = SQLiteStorage(DATABASE.get("sqlite_path", "barber.db"))
    return _storage


__all__ = ["get_storage", "Storage", "Appointment"]
