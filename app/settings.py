"""Конфигурация бота: читаем YAML, валидируем и отдаём типизированный объект.

Раньше настройки лежали в config.py и правились руками в коде. Теперь всё
описано в config.yml, а здесь мы один раз при старте проверяем, что конфиг
не противоречит сам себе (например, мастер ссылается на несуществующую услугу),
чтобы бот не падал уже в середине записи клиента.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent


class ConfigError(RuntimeError):
    """Конфиг кривой - падаем громко и сразу, а не по кусочкам в рантайме."""


def _read_yaml(filename: str) -> dict[str, Any]:
    path = BASE_DIR / filename
    if not path.exists():
        raise ConfigError(f"не найден файл {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"{filename}: на верхнем уровне ожидался словарь")
    return data


def _section(raw: dict[str, Any], key: str, where: str) -> dict[str, Any]:
    """Достаём вложенный блок, не падая на его отсутствии."""
    value = raw.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"{where}.{key}: ожидался блок настроек")
    return value


def _req(raw: dict[str, Any], key: str, where: str) -> Any:
    if key not in raw or raw[key] in (None, ""):
        raise ConfigError(f"{where}: обязательное поле '{key}' не заполнено")
    return raw[key]


@dataclass(frozen=True)
class Service:
    id: str
    name: str
    emoji: str
    price: int
    duration: int
    description: str = ""


@dataclass(frozen=True)
class Master:
    id: str
    name: str
    emoji: str
    specialization: str
    experience: int
    services: tuple[str, ...]


@dataclass(frozen=True)
class Shop:
    name: str
    tagline: str
    address: str
    phone: str
    work_hours: str
    instagram: str
    map_url: str
    about: str


@dataclass(frozen=True)
class BotCfg:
    token: str
    name: str
    timezone: str
    currency: str
    admins: frozenset[int]
    support_username: str


@dataclass(frozen=True)
class MySQLCfg:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass(frozen=True)
class DatabaseCfg:
    type: str
    sqlite_path: str
    mysql: MySQLCfg


@dataclass(frozen=True)
class BookingCfg:
    work_start: str
    work_end: str
    slot_step: int
    days_ahead: int
    late_options: tuple[int, ...]


@dataclass(frozen=True)
class RemindersCfg:
    enabled: bool
    hours_before: int
    poll_minutes: int


@dataclass(frozen=True)
class PaymentCfg:
    onsite: bool
    online_enabled: bool
    provider: str


@dataclass(frozen=True)
class Settings:
    bot: BotCfg
    shop: Shop
    database: DatabaseCfg
    booking: BookingCfg
    reminders: RemindersCfg
    payments: PaymentCfg
    services: dict[str, Service] = field(default_factory=dict)
    masters: dict[str, Master] = field(default_factory=dict)

    # ── удобные выборки, чтобы хендлеры не лазили в словари напрямую ──
    def service(self, service_id: str) -> Service:
        try:
            return self.services[service_id]
        except KeyError:
            raise ConfigError(f"услуга '{service_id}' не описана в config.yml") from None

    def master(self, master_id: str) -> Master:
        try:
            return self.masters[master_id]
        except KeyError:
            raise ConfigError(f"мастер '{master_id}' не описан в config.yml") from None

    def services_for(self, master_id: str) -> list[Service]:
        """Только те услуги, которые мастер реально делает."""
        master = self.master(master_id)
        return [self.services[s] for s in master.services if s in self.services]

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.bot.admins

    @property
    def currency(self) -> str:
        return self.bot.currency


# ──────────────────────── парсинг ────────────────────────
def _parse_services(raw: dict[str, Any]) -> dict[str, Service]:
    if not raw:
        raise ConfigError("config.yml: не описано ни одной услуги")
    result: dict[str, Service] = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            raise ConfigError(f"config.yml: услуга '{key}' должна быть словарём")
        price = int(_req(value, "price", f"services.{key}"))
        duration = int(_req(value, "duration", f"services.{key}"))
        if price < 0 or duration <= 0:
            raise ConfigError(f"services.{key}: цена >= 0, длительность > 0")
        result[str(key)] = Service(
            id=str(key),
            name=str(_req(value, "name", f"services.{key}")),
            emoji=str(value.get("emoji", "✂️")),
            price=price,
            duration=duration,
            description=str(value.get("description", "")),
        )
    return result


def _parse_masters(raw: dict[str, Any], services: dict[str, Service]) -> dict[str, Master]:
    if not raw:
        raise ConfigError("config.yml: не описано ни одного мастера")
    result: dict[str, Master] = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            raise ConfigError(f"config.yml: мастер '{key}' должен быть словарём")
        own_services = tuple(str(s) for s in value.get("services") or [])
        if not own_services:
            raise ConfigError(f"masters.{key}: список services пуст")
        unknown = [s for s in own_services if s not in services]
        if unknown:
            # Классическая ошибка при ручном правлении YAML - ловим на старте.
            raise ConfigError(f"masters.{key}: неизвестные услуги {unknown}")
        result[str(key)] = Master(
            id=str(key),
            name=str(_req(value, "name", f"masters.{key}")),
            emoji=str(value.get("emoji", "💈")),
            specialization=str(value.get("specialization", "")),
            experience=int(value.get("experience", 0)),
            services=own_services,
        )
    return result


def _env_admins(fallback: list[Any]) -> frozenset[int]:
    """ADMINS=111,222 в .env перекрывает список из YAML - удобно на сервере."""
    raw = os.getenv("ADMINS", "").replace(";", ",")
    source = raw.split(",") if raw.strip() else fallback
    ids: set[int] = set()
    for item in source:
        item = str(item).strip()
        if item.isdigit():
            ids.add(int(item))
    return frozenset(ids)


def load_settings() -> Settings:
    raw = _read_yaml("config.yml")

    bot_raw = _section(raw, "bot", "config.yml")
    shop_raw = _section(raw, "shop", "config.yml")
    db_raw = _section(raw, "database", "config.yml")
    booking_raw = _section(raw, "booking", "config.yml")
    remind_raw = _section(raw, "reminders", "config.yml")
    pay_raw = _section(raw, "payments", "config.yml")
    online_raw = _section(pay_raw, "online", "payments")
    mysql_raw = _section(db_raw, "mysql", "database")

    services = _parse_services(_section(raw, "services", "config.yml"))
    masters = _parse_masters(_section(raw, "masters", "config.yml"), services)

    token = (os.getenv("BOT_TOKEN") or bot_raw.get("token") or "").strip()

    return Settings(
        bot=BotCfg(
            token=token,
            name=str(bot_raw.get("name") or "BarberShop"),
            timezone=str(bot_raw.get("timezone") or "Europe/Moscow"),
            currency=str(bot_raw.get("currency") or "BYN"),
            admins=_env_admins(list(bot_raw.get("admins") or [])),
            support_username=str(bot_raw.get("support_username") or "support"),
        ),
        shop=Shop(
            name=str(shop_raw.get("name") or bot_raw.get("name") or "BarberShop"),
            tagline=str(shop_raw.get("tagline") or ""),
            address=str(shop_raw.get("address") or ""),
            phone=str(shop_raw.get("phone") or ""),
            work_hours=str(shop_raw.get("work_hours") or ""),
            instagram=str(shop_raw.get("instagram") or ""),
            map_url=str(shop_raw.get("map_url") or ""),
            about=str(shop_raw.get("about") or ""),
        ),
        database=DatabaseCfg(
            type=str(db_raw.get("type") or "sqlite").lower(),
            sqlite_path=str(os.getenv("SQLITE_PATH") or db_raw.get("sqlite_path") or "barber.db"),
            mysql=MySQLCfg(
                host=str(os.getenv("MYSQL_HOST") or mysql_raw.get("host") or "127.0.0.1"),
                port=int(os.getenv("MYSQL_PORT") or mysql_raw.get("port") or 3306),
                user=str(os.getenv("MYSQL_USER") or mysql_raw.get("user") or "barber"),
                password=str(os.getenv("MYSQL_PASSWORD") or mysql_raw.get("password") or ""),
                database=str(os.getenv("MYSQL_DATABASE") or mysql_raw.get("database") or "barber"),
            ),
        ),
        booking=BookingCfg(
            work_start=str(booking_raw.get("work_start") or "10:00"),
            work_end=str(booking_raw.get("work_end") or "21:00"),
            slot_step=int(booking_raw.get("slot_step") or 30),
            days_ahead=int(booking_raw.get("days_ahead") or 14),
            late_options=tuple(int(x) for x in (booking_raw.get("late_options") or [5, 10, 15])),
        ),
        reminders=RemindersCfg(
            enabled=bool(remind_raw.get("enabled", True)),
            hours_before=int(remind_raw.get("hours_before") or 3),
            poll_minutes=int(remind_raw.get("poll_minutes") or 5),
        ),
        payments=PaymentCfg(
            onsite=bool(pay_raw.get("onsite", True)),
            online_enabled=bool(online_raw.get("enabled", False)),
            provider=str(online_raw.get("provider") or "yookassa"),
        ),
        services=services,
        masters=masters,
    )


settings: Settings = load_settings()
