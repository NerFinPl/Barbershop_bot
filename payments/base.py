"""Базовый интерфейс платёжного провайдера."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PaymentResult:
    ok: bool
    pay_url: str | None = None       # ссылка на оплату
    payment_id: str | None = None    # id платежа на стороне провайдера
    error: str | None = None


class PaymentProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def create_payment(self, amount: int, description: str, payload: str) -> PaymentResult: ...
