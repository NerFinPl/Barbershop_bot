"""Реализация хранилища на MySQL (aiomysql). Включается через config.DATABASE['type'] = 'mysql'."""
from __future__ import annotations

import os
from typing import Any

import aiomysql

from .base import Appointment, Storage


def _row_to_appt(row: dict) -> Appointment:
    return Appointment(**row)


class MySQLStorage(Storage):
    def __init__(self, cfg: dict[str, Any]) -> None:
        # Пароль/юзер можно переопределить из .env
        self.cfg = {
            "host": os.getenv("MYSQL_HOST", cfg.get("host", "127.0.0.1")),
            "port": int(os.getenv("MYSQL_PORT", cfg.get("port", 3306))),
            "user": os.getenv("MYSQL_USER", cfg.get("user", "barber")),
            "password": os.getenv("MYSQL_PASSWORD", cfg.get("password", "barber")),
            "db": os.getenv("MYSQL_DATABASE", cfg.get("database", "barber")),
        }
        self._pool: aiomysql.Pool | None = None

    async def init(self) -> None:
        self._pool = await aiomysql.create_pool(
            **self.cfg, autocommit=True, minsize=1, maxsize=5, charset="utf8mb4"
        )
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS appointments (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        master_id VARCHAR(64) NOT NULL,
                        service_id VARCHAR(64) NOT NULL,
                        date DATE NOT NULL,
                        time VARCHAR(8) NOT NULL,
                        price INT NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        phone VARCHAR(32) NOT NULL,
                        status VARCHAR(16) DEFAULT 'active',
                        payment VARCHAR(16) DEFAULT 'none',
                        payment_id VARCHAR(128),
                        late_minutes INT DEFAULT 0,
                        reminded TINYINT DEFAULT 0,
                        created_at DATETIME NOT NULL
                    ) CHARACTER SET utf8mb4
                    """
                )

    async def create_appointment(self, **kwargs: Any) -> int:
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join("%s" for _ in kwargs)
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"INSERT INTO appointments ({cols}) VALUES ({placeholders})",
                    tuple(kwargs.values()),
                )
                return int(cur.lastrowid)

    async def get_appointment(self, appointment_id: int) -> Appointment | None:
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM appointments WHERE id=%s", (appointment_id,))
                row = await cur.fetchone()
        return _row_to_appt(self._normalize(row)) if row else None

    async def user_appointments(self, user_id: int, only_active: bool = True) -> list[Appointment]:
        sql = "SELECT * FROM appointments WHERE user_id=%s"
        if only_active:
            sql += " AND status='active'"
        sql += " ORDER BY date, time"
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, (user_id,))
                rows = await cur.fetchall()
        return [_row_to_appt(self._normalize(r)) for r in rows]

    async def taken_slots(self, master_id: str, date_iso: str) -> set[str]:
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT time FROM appointments WHERE master_id=%s AND date=%s AND status='active'",
                    (master_id, date_iso),
                )
                rows = await cur.fetchall()
        return {r[0] for r in rows}

    async def update_appointment(self, appointment_id: int, **fields: Any) -> None:
        if not fields:
            return
        sets = ", ".join(f"{k}=%s" for k in fields)
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"UPDATE appointments SET {sets} WHERE id=%s",
                    (*fields.values(), appointment_id),
                )

    async def due_reminders(self, now_iso: str, window_iso: str) -> list[Appointment]:
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM appointments WHERE status='active' AND reminded=0 "
                    "AND TIMESTAMP(date, time) BETWEEN %s AND %s",
                    (now_iso, window_iso),
                )
                rows = await cur.fetchall()
        return [_row_to_appt(self._normalize(r)) for r in rows]

    async def mark_reminded(self, appointment_id: int) -> None:
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE appointments SET reminded=1 WHERE id=%s", (appointment_id,)
                )

    @staticmethod
    def _normalize(row: dict) -> dict:
        """MySQL отдаёт date как datetime.date, а нам стабильно нужен ISO-стринг."""
        row = dict(row)
        if hasattr(row.get("date"), "isoformat"):
            row["date"] = row["date"].isoformat()
        if row.get("created_at") and not isinstance(row["created_at"], str):
            row["created_at"] = row["created_at"].isoformat()
        return row
