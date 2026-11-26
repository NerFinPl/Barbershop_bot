"""BePaY (Беларусь). Ключи только из .env, в коде их быть не должно.

Если мерчант-данные не заданы - возвращаем ok=False, бот предложит оплату на месте.
"""
from __future__ import annotations

import os
import uuid

import aiohttp

from .base import PaymentProvider, PaymentResult

BEPAY_API = "https://api.bepay.by/v1/payments"  # пример эндпоинта, сверьтесь с докой мерчанта


class BePayProvider(PaymentProvider):
    name = "bepay"

    async def create_payment(self, amount: int, description: str, payload: str) -> PaymentResult:
        merchant_id = os.getenv("BEPAY_MERCHANT_ID", "").strip()
        token = os.getenv("BEPAY_TOKEN", "").strip()
        if not merchant_id or not token:
            return PaymentResult(ok=False, error="BePaY не настроен (нет ключей в .env)")

        body = {
            "merchant_id": merchant_id,
            "order_id": payload,
            "amount": amount,
            "currency": "BYN",
            "description": description,
            "return_url": os.getenv("BEPAY_RETURN_URL", ""),
            "idempotency_key": uuid.uuid4().hex,
        }
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(BEPAY_API, json=body, headers=headers, timeout=15) as resp:
                    data = await resp.json(content_type=None)
                    if resp.status >= 400:
                        return PaymentResult(ok=False, error=str(data))
        except Exception as exc:  # сеть/таймаут - не роняем бота
            return PaymentResult(ok=False, error=f"BePaY: {exc}")

        pay_url = data.get("redirect_url") or data.get("payment_url") or data.get("url")
        payment_id = str(data.get("payment_id") or data.get("id") or "")
        if not pay_url:
            return PaymentResult(ok=False, error="BePaY не вернул ссылку на оплату")
        return PaymentResult(ok=True, pay_url=pay_url, payment_id=payment_id or None)
