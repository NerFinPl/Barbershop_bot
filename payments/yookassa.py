"""ЮKassa (Россия). BasicAuth по shop_id + secret_key, ключи - из .env."""
from __future__ import annotations

import os
import uuid

import aiohttp

from .base import PaymentProvider, PaymentResult

YOOKASSA_API = "https://api.yookassa.ru/v3/payments"


class YooKassaProvider(PaymentProvider):
    name = "yookassa"

    async def create_payment(self, amount: int, description: str, payload: str) -> PaymentResult:
        shop_id = os.getenv("YOOKASSA_SHOP_ID", "").strip()
        secret = os.getenv("YOOKASSA_SECRET_KEY", "").strip()
        if not shop_id or not secret:
            return PaymentResult(ok=False, error="ЮKassa не настроена (нет ключей в .env)")

        body = {
            "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
            "capture": True,
            "description": description[:128],
            "confirmation": {
                "type": "redirect",
                "return_url": os.getenv("YOOKASSA_RETURN_URL", "https://t.me/"),
            },
            "metadata": {"payload": payload},
        }
        headers = {"Idempotence-Key": uuid.uuid4().hex, "Content-Type": "application/json"}

        try:
            async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(shop_id, secret)) as session:
                async with session.post(YOOKASSA_API, json=body, headers=headers, timeout=15) as resp:
                    data = await resp.json(content_type=None)
                    if resp.status >= 400:
                        return PaymentResult(ok=False, error=str(data))
        except Exception as exc:
            return PaymentResult(ok=False, error=f"ЮKassa: {exc}")

        conf = data.get("confirmation") or {}
        pay_url = conf.get("confirmation_url")
        if not pay_url:
            return PaymentResult(ok=False, error="ЮKassa не вернула confirmation_url")
        return PaymentResult(ok=True, pay_url=pay_url, payment_id=data.get("id"))
