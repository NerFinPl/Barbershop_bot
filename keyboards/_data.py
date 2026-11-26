"""Единая точка доступа к справочникам для клавиатур.

Клавиатуры - единственное место, которое пока тянет данные напрямую. Хендлеры
потихоньку уезжают на app.settings, а тут я держу прослойку: сначала пробуем
новый конфиг из config.yml, если он почему-то не поднялся - откатываемся на
старый config.py. Так клавиатуры не падают в переходный период, а когда старый
конфиг выпилим, отсюда уйдёт ровно один блок.
"""
from __future__ import annotations

from typing import Any


_CATALOG: tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]] | None = None


def _attrs(obj: Any) -> dict[str, Any]:
    """Приводим dataclass, словарь или строку из БД к обычному словарю."""
    if obj is None:
        return {}
    if hasattr(obj, "to_dict"):
        return dict(obj.to_dict())
    if isinstance(obj, dict):
        return dict(obj)
    return dict(getattr(obj, "__dict__", {}) or {})


def _as_service(sid: str, obj: Any) -> dict[str, Any]:
    raw = _attrs(obj)
    return {
        "id": sid,
        "name": raw.get("name") or sid,
        "emoji": raw.get("emoji") or "✂️",
        "price": raw.get("price"),
        "duration": raw.get("duration"),
        "description": raw.get("description") or "",
    }


def _as_master(mid: str, obj: Any) -> dict[str, Any]:
    raw = _attrs(obj)
    linked = raw.get("services") or ()
    # В yaml это список, но если кто-то напишет одну услугу строкой - не падаем.
    if isinstance(linked, str):
        linked = (linked,)
    return {
        "id": mid,
        "name": raw.get("name") or mid,
        "emoji": raw.get("emoji") or "💈",
        "specialization": raw.get("specialization") or "",
        "experience": raw.get("experience"),
        "services": [str(item) for item in linked],
    }


def _from_settings() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Новый путь: app.settings уже свалидирован на старте."""
    try:
        from app import settings  # импорт ленивый намеренно: конфиг может не подняться
    except Exception:  # noqa: BLE001
        return {}, {}

    masters_raw = _attrs(getattr(settings, "masters", None))
    services_raw = _attrs(getattr(settings, "services", None))

    masters = {key: _as_master(key, value) for key, value in masters_raw.items()}
    services = {key: _as_service(key, value) for key, value in services_raw.items()}
    return masters, services


def _from_config() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Старый путь - пока жив config.py."""
    try:
        from config import MASTERS, SERVICES  # noqa: BLE001
    except Exception:
        return {}, {}
    return dict(MASTERS or {}), dict(SERVICES or {})


def _build() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    masters, services = _from_settings()
    if masters and services:
        return masters, services

    old_masters, old_services = _from_config()
    # Смешивать не стал: если новый конфиг отдал половину, доверять ему всё равно нельзя.
    return old_masters, old_services


def catalog() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Мастера и услуги одним куском. Кэш на процесс - YAML зря не дёргаем."""
    global _CATALOG
    if _CATALOG is None:
        _CATALOG = _build()
    return _CATALOG


def masters() -> dict[str, dict[str, Any]]:
    return catalog()[0]


def services() -> dict[str, dict[str, Any]]:
    return catalog()[1]


def master(master_id: str) -> dict[str, Any]:
    return masters().get(master_id) or {}


def service(service_id: str) -> dict[str, Any]:
    return services().get(service_id) or {}


def payments() -> dict[str, dict[str, Any]]:
    """Платёжные провайдеры пока живут только в старом конфиге."""
    try:
        from config import PAYMENTS  # noqa: BLE001
    except Exception:
        return {}
    return dict(PAYMENTS or {})


def reset_cache() -> None:
    """Пригодится в тестах: подменили конфиг - сбросили кэш."""
    global _CATALOG
    _CATALOG = None
