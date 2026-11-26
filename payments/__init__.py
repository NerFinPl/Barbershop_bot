"""Платёжный слой: фабрика провайдеров по config.PAYMENTS."""
from __future__ import annotations

from .base import PaymentProvider, PaymentResult


def get_provider(name: str) -> PaymentProvider | None:
    name = name.lower()
    if name == "bepay":
        from .bepay import BePayProvider

        return BePayProvider()
    if name == "yookassa":
        from .yookassa import YooKassaProvider

        return YooKassaProvider()
    return None


__all__ = ["PaymentProvider", "PaymentResult", "get_provider"]
