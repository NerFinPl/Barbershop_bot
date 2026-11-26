"""Абстракция БД. Все запросы к данным идут только через этот интерфейс,
поэтому переключение SQLite <-> MySQL не задевает логику хендлеров."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Appointment:
    """Одна запись клиента. Именно этот объект гуляет по коду."""

    id: int
    user_id: int
    master_id: str
    service_id: str
    date: str            # ISO date, например "2024-06-03"
    time: str            # "15:00"
    price: int
    name: str
    phone: str
    status: str = "active"           # active | cancelled | done
    payment: str = "none"            # none | online | onsite
    payment_id: str | None = None
    late_minutes: int = 0
    reminded: int = 0                # флаг: напоминание уже отправлено
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class Storage(ABC):
    """Минимальный набор операций, который нужен боту."""

    @abstractmethod
    async def init(self) -> None: ...

    @abstractmethod
    async def create_appointment(self, **kwargs: Any) -> int: ...

    @abstractmethod
    async def get_appointment(self, appointment_id: int) -> Appointment | None: ...

    @abstractmethod
    async def user_appointments(self, user_id: int, only_active: bool = True) -> list[Appointment]: ...

    @abstractmethod
    async def taken_slots(self, master_id: str, date_iso: str) -> set[str]: ...

    @abstractmethod
    async def update_appointment(self, appointment_id: int, **fields: Any) -> None: ...

    @abstractmethod
    async def due_reminders(self, now_iso: str, window_iso: str) -> list[Appointment]: ...

    @abstractmethod
    async def mark_reminded(self, appointment_id: int) -> None: ...
