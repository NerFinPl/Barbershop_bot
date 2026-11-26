"""Роутеры бота. Порядок подключения важен: более конкретные - первыми."""
from . import booking, info, records, start  # noqa: F401

__all__ = ["start", "booking", "records", "info"]
