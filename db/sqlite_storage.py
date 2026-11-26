"""Реализация хранилища на SQLite (по умолчанию)."""
from __future__ import annotations

from typing import Any

import aiosqlite

from .base import Appointment, Storage


def _row_to_appt(row: Any) -> Appointment:
    keys = row.keys()
    data = {k: row[k] for k in keys}
    return Appointment(**data)


class SQLiteStorage(Storage):
    def __init__(self, path: str) -> None:
        self.path = path
        self._conn: aiosqlite.Connection | None = None

    async def init(self) -> None:
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                master_id TEXT NOT NULL,
                service_id TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                price INTEGER NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                payment TEXT DEFAULT 'none',
                payment_id TEXT,
                late_minutes INTEGER DEFAULT 0,
                reminded INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        await self._conn.commit()

    async def create_appointment(self, **kwargs: Any) -> int:
        # created_at есть в kwargs (приходит из Appointment._defaults)
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join("?" for _ in kwargs)
        cur = await self._conn.execute(
            f"INSERT INTO appointments ({cols}) VALUES ({placeholders})",
            tuple(kwargs.values()),
        )
        await self._conn.commit()
        return int(cur.lastrowid)

    async def get_appointment(self, appointment_id: int) -> Appointment | None:
        cur = await self._conn.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
        row = await cur.fetchone()
        return _row_to_appt(row) if row else None

    async def user_appointments(self, user_id: int, only_active: bool = True) -> list[Appointment]:
        sql = "SELECT * FROM appointments WHERE user_id = ?"
        if only_active:
            sql += " AND status = 'active'"
        sql += " ORDER BY date, time"
        cur = await self._conn.execute(sql, (user_id,))
        rows = await cur.fetchall()
        return [_row_to_appt(r) for r in rows]

    async def taken_slots(self, master_id: str, date_iso: str) -> set[str]:
        cur = await self._conn.execute(
            "SELECT time FROM appointments WHERE master_id = ? AND date = ? AND status = 'active'",
            (master_id, date_iso),
        )
        rows = await cur.fetchall()
        return {r["time"] for r in rows}

    async def update_appointment(self, appointment_id: int, **fields: Any) -> None:
        if not fields:
            return
        sets = ", ".join(f"{k} = ?" for k in fields)
        await self._conn.execute(
            f"UPDATE appointments SET {sets} WHERE id = ?",
            (*fields.values(), appointment_id),
        )
        await self._conn.commit()

    async def due_reminders(self, now_iso: str, window_iso: str) -> list[Appointment]:
        # Берём активные записи, у которых дата+время попадают в окно напоминания.
        cur = await self._conn.execute(
            "SELECT * FROM appointments WHERE status = 'active' AND reminded = 0 "
            "AND (date || ' ' || time) BETWEEN ? AND ?",
            (now_iso, window_iso),
        )
        rows = await cur.fetchall()
        return [_row_to_appt(r) for r in rows]

    async def mark_reminded(self, appointment_id: int) -> None:
        await self._conn.execute(
            "UPDATE appointments SET reminded = 1 WHERE id = ?", (appointment_id,)
        )
        await self._conn.commit()
