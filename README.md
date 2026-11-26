# 💈 Barber & Co — Telegram-бот записи для барбершопа

Готовый бот на **aiogram 3.x**: запись к мастеру, «Мои записи» с переносом/отменой,
«Я опоздаю», онлайн-оплата (BePaY и ЮKassa) или оплата на месте, напоминания,
поддержка. Всё настраивается через `config.py`, секреты — в `.env`.

---

## 📁 Структура

```
BarberShopBot/
├── bot.py                 # точка входа
├── config.py              # услуги, мастера, цены, оплата, напоминания — всё здесь
├── messages.py            # все тексты и подписи кнопок
├── .env.example           # шаблон секретов
├── requirements.txt
├── handlers/              # start, booking, records, payment, info
├── keyboards/             # main, booking, records, pay
├── services/              # слоты, валидация, напоминания, уведомления
├── payments/              # base, bepay, yookassa + фабрика
└── db/                    # base (ABC) + sqlite + mysql
```

Смена БД — одна строка в `config.py`:

```python
DATABASE = {"type": "sqlite", ...}   # или "mysql"
```

---

## 🚀 Установка

```bash
cd BarberShopBot
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Настройка `.env`

```bash
cp .env.example .env
```

Заполните минимум:

```env
BOT_TOKEN=123456789:AAE-...        # от @BotFather
ADMIN_CHAT_ID=123456789            # куда присылать уведомления (опционально)
```

Оплата (можно оставить пустой — тогда бот просто предложит оплату на месте):

```env
# ЮKassa
YOOKASSA_SHOP_ID=
YOOKASSA_SECRET_KEY=
YOOKASSA_RETURN_URL=https://t.me/your_bot

# BePaY
BEPAY_MERCHANT_ID=
BEPAY_TOKEN=
BEPAY_RETURN_URL=https://t.me/your_bot
```

### Запуск

```bash
python bot.py
```

---

## ⚙️ Настройка бизнес-логики

Всё в `config.py`, перезапуск нужен только после изменения:

| Что | Где |
|---|---|
| Услуги, цены, длительность | `SERVICES` |
| Мастера и их набор услуг | `MASTERS[*]["services"]` |
| Рабочие часы, шаг сетки, дней вперёд | `BOOKING` |
| Варианты «я опоздаю» | `LATE_OPTIONS` |
| За сколько напоминать | `REMINDER["before_minutes"]` |
| Включить/выключить оплату | `PAYMENTS[*]["enabled"]` |
| Тексты кнопок | `BUTTONS` |
| Поддержка | `SUPPORT` |

**Добавить услугу** — просто новый ключ в `SERVICES` и добавить его id в `MASTERS[*]["services"]`. Код не трогаем.

---

## 🔔 Напоминания

APScheduler раз в минуту проверяет БД и отправляет сообщение за
`REMINDER["before_minutes"]` до визита. Флаг `reminded` в БД защищает от дублей.

---

## 💳 Оплата

- **BePaY** — `payments/bepay.py`, эндпоинт и поля сверяйте с актуальной докой мерчанта.
- **ЮKassa** — `payments/yookassa.py`, стандартный `/v3/payments` с BasicAuth.
- Ключи **только** в `.env`, в репозиторий не попадают.
- Если ключи не заданы — провайдер вернёт ошибку, бот предложит оплату на месте.

Для продакшена добавьте вебхук-эндпоинт провайдера и обновляйте `payment_id`/статус записи.

---

## 🛠 Мелочи

- Телефон нормализуется к виду `+375291234567`, валидируется 10–15 цифр.
- Имя: 2–40 символов, буквы/пробел/дефис/апостроф.
- Статусы записи: `active` → `cancelled`. `late_minutes` хранит опоздание.
- Уведомления админу (опоздание/отмена) идут, только если задан `ADMIN_CHAT_ID`.
- Пароль MySQL можно переопределить из `.env` (`MYSQL_*`).
