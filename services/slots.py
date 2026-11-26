"""Логика свободных слотов: сетка времени + вычитание занятых."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from config import BOOKING, MASTERS, TIMEZONE


def _parse_hm(value: str) -> tuple[int, int]:
    h, m = value.split(":")
    return int(h), int(m)


def day_grid(date_iso: str) -> list[str]:
    """Сетка рабочих часов с шагом BOOKING['slot_step']."""
    sh, sm = _parse_hm(BOOKING["work_start"])
    eh, em = _parse_hm(BOOKING["work_end"])
    start = datetime.combine(date.fromisoformat(date_iso), datetime.min.time()).replace(hour=sh, minute=sm)
    end = datetime.combine(date.fromisoformat(date_iso), datetime.min.time()).replace(hour=eh, minute=em)
    step = timedelta(minutes=BOOKING["slot_step"])
    slots = []
    t = start
    while t <= end:
        slots.append(t.strftime("%H:%M"))
        t += step
    return slots


def free_slots(date_iso: str, taken: set[str], duration_min: int = 0) -> list[str]:
    """Убираем уже занятые окна.
    Если услуга длинная - отсекаем слоты, где она не влезет до закрытия.
    (Пока простое вычитание: пересечения длительности учитываем через занятые окна мастера.)
    """
    grid = day_grid(date_iso)
    # Отсекаем прошедшее время, если листаем «сегодня»
    now = datetime.now()
    if date_iso == date.today().isoformat():
        grid = [s for s in grid if datetime.strptime(f"{date_iso} {s}", "%Y-%m-%d %H:%M") > now]
    # Отсекаем слоты, где услуга не доедет до конца рабочего дня
    eh, em = _parse_hm(BOOKING["work_end"])
    close = datetime.strptime(f"{date_iso} {eh:02d}:{em:02d}", "%Y-%m-%d %H:%M")
    result = []
    for s in grid:
        if duration_min:
            start = datetime.strptime(f"{date_iso} {s}", "%Y-%m-%d %H:%M")
            if start + timedelta(minutes=duration_min) > close:
                continue
        if s not in taken:
            result.append(s)
    return result
