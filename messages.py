"""Все тексты сообщений бота. Меняем копирайт - правим только этот файл."""
from __future__ import annotations

from config import CURRENCY, LATE_OPTIONS, MASTERS, REMINDER, SERVICES, SHOP, SUPPORT
from services.utils import human_date, money


class M:
    """Единая точка входа за текстом: M.welcome(...), M.card(...) и т.д."""

    # ── главный экран ────────────────────────────────────────────────
    @staticmethod
    def welcome(name: str) -> str:
        return (
            f"👋 <b>{name}</b>, добро пожаловать в <b>{SHOP['name']}</b>!\n"
            f"<i>{SHOP['tagline']}</i>\n\n"
            f"📍 {SHOP['address']}\n"
            f"🕐 {SHOP['work_hours']}\n\n"
            "Выберите, что нужно - запишу за минуту 👇"
        )

    menu_hint = "🏠 Главное меню - выбирайте действие 👇"

    # ── запись ───────────────────────────────────────────────────────
    choose_master = "💈 <b>Шаг 1 из 4.</b> Выберите мастера:"
    choose_date = "📅 <b>Шаг 3 из 4.</b> На какой день планируете визит?"

    @staticmethod
    def choose_service(master_id: str) -> str:
        m = MASTERS[master_id]
        return f"✂️ <b>Шаг 2 из 4.</b> Что делает {m['name']}? Выберите услугу:"

    @staticmethod
    def choose_time(date_iso: str, slots_count: int) -> str:
        return (
            f"🕐 <b>Шаг 3 из 4.</b> {human_date(date_iso)} - свободно {slots_count} окошек.\n"
            "Выберите удобное время:"
        )

    ask_name = "📝 <b>Шаг 4 из 4.</b> Как вас зовут? Напишите имя одним сообщением."
    bad_name = "🤔 Кажется, это не имя. Напишите, пожалуйста, от 2 до 40 символов."
    ask_phone = (
        "📱 Оставьте номер телефона - мастер позвонит, если что-то изменится.\n"
        "Можно нажать кнопку ниже или ввести вручную (+375 29 123-45-67)."
    )
    bad_phone = "🤔 Номер не распознан. Пример: <code>+375 29 123-45-67</code>"

    @staticmethod
    def card(master_id: str, service_id: str, date_iso: str, time_str: str, price: int) -> str:
        m, s = MASTERS[master_id], SERVICES[service_id]
        return (
            f"{s['emoji']} <b>{s['name']}</b>\n"
            f"👤 Мастер: <b>{m['name']}</b> · {m['title']}\n"
            f"📅 {human_date(date_iso)} · <b>{time_str}</b>\n"
            f"⏱ {s['duration']} мин · 💰 <b>{money(price, CURRENCY)}</b>"
        )

    @staticmethod
    def confirm(card_text: str, name: str, phone: str) -> str:
        return (
            "🧾 <b>Проверьте запись</b>\n\n"
            f"{card_text}\n\n"
            f"🙋 Имя: <b>{name}</b>\n"
            f"📞 Телефон: <b>{phone}</b>\n\n"
            "Всё верно?"
        )

    @staticmethod
    def saved(card_text: str) -> str:
        remind = REMINDER["before_minutes"]
        hours = remind // 60
        remind_text = f"за {hours} ч." if hours and remind % 60 == 0 else f"за {remind} мин."
        return (
            "✅ <b>Запись создана!</b>\n\n"
            f"{card_text}\n\n"
            f"🔔 Напомним {remind_text} до визита.\n"
            "Если планы поменяются - загляните в «Мои записи»."
        )

    paid_online = "💳 <b>Оплата принята</b> - спасибо! Ждём вас."
    pay_onsite = "💵 Хорошо, оплатите на месте. Не забудьте про наличные или карту."
    pay_title = "💳 <b>Как удобнее оплатить?</b>"
    pay_failed = "😔 Не получилось создать платёж. Попробуйте ещё раз или оплатите на месте."

    @staticmethod
    def pay_link(amount: int, currency: str) -> str:
        return f"💳 Сумма к оплате: <b>{money(amount, currency)}</b>. Нажмите кнопку ниже 👇"

    # ── список записей ───────────────────────────────────────────────
    no_records = (
        "📭 У вас пока нет активных записей.\n\n"
        "Самое время это исправить - жмите «📅 Записаться»."
    )

    @staticmethod
    def my_records(rows: list[dict]) -> str:
        lines = ["🗓 <b>Ваши записи</b>\n"]
        for i, r in enumerate(rows, 1):
            s = SERVICES.get(r["service_id"], {"emoji": "•", "name": r["service_id"]})
            m = MASTERS.get(r["master_id"], {"name": r["master_id"]})
            lines.append(
                f"{i}. {s['emoji']} <b>{s['name']}</b> - {human_date(r['date'])} в {r['time']}\n"
                f"    👤 {m['name']} · {money(r.get('price', 0), CURRENCY)}"
            )
        lines.append("\nНажмите на номер, чтобы открыть карточку.")
        return "\n".join(lines)

    @staticmethod
    def record_card(r: dict) -> str:
        s = SERVICES.get(r["service_id"], {"emoji": "•", "name": r["service_id"], "duration": 0})
        m = MASTERS.get(r["master_id"], {"name": r["master_id"], "title": ""})
        pay = {"online": "оплачено онлайн 💳", "onsite": "оплата на месте 💵"}.get(
            r.get("payment"), "оплата не выбрана"
        )
        late = f"\n⏰ Предупредили об опоздании на {r['late_minutes']} мин." if r.get("late_minutes") else ""
        return (
            f"🧾 <b>Ваша запись</b>\n\n"
            f"{s['emoji']} <b>{s['name']}</b>\n"
            f"👤 Мастер: <b>{m['name']}</b> · {m.get('title', '')}\n"
            f"📅 {human_date(r['date'])} · <b>{r['time']}</b>\n"
            f"💰 {money(r.get('price', 0), CURRENCY)} · {pay}{late}"
        )

    cancel_ask = "❓ Точно отменяем запись? Место освободится для других гостей."
    cancelled = "❌ Запись отменена. Будем рады видеть вас в другой раз!"
    not_found = "🤷 Запись не найдена - возможно, она уже отменена."

    @staticmethod
    def late_ask() -> str:
        options = ", ".join(str(x) for x in LATE_OPTIONS)
        return f"⏰ На сколько вы задержитесь? Варианты: {options} мин."

    @staticmethod
    def late_done(minutes: int) -> str:
        return (
            f"🙏 Спасибо, что предупредили! Передали мастеру - вас подождут {minutes} мин.\n"
            "Если планы снова изменятся, просто зайдите в «Мои записи»."
        )

    # ── перенос ──────────────────────────────────────────────────────
    move_master = "🔄 Выберите нового мастера (или оставьте прежнего):"
    move_date = "🔄 На какой день переносим?"

    @staticmethod
    def move_time(date_iso: str) -> str:
        return f"🔄 {human_date(date_iso)} - выберите новое время:"

    @staticmethod
    def moved(card_text: str) -> str:
        return f"🔄 <b>Запись перенесена!</b>\n\n{card_text}"

    slot_taken = "😔 Это время только что заняли. Выберите другое."
    no_slots = "😔 На этот день свободных окон не осталось. Попробуйте другую дату."

    # ── напоминание ──────────────────────────────────────────────────
    @staticmethod
    def reminder(appt: dict) -> str:
        s = SERVICES.get(appt["service_id"], {"name": appt["service_id"]})
        m = MASTERS.get(appt["master_id"], {"name": appt["master_id"]})
        return (
            f"🔔 <b>Напоминаем:</b> вы записаны на {s['name'].lower()} "
            f"к мастеру {m['name']} в {appt['time']}.\n"
            f"📅 {human_date(appt['date'])}"
        )

    # ── инфо-разделы ─────────────────────────────────────────────────
    @staticmethod
    def services_list() -> str:
        lines = ["✂️ <b>Услуги и цены</b>\n"]
        for s in SERVICES.values():
            lines.append(
                f"{s['emoji']} <b>{s['name']}</b> - {money(s['price'], CURRENCY)}\n"
                f"    <i>{s['duration']} мин · {s['description']}</i>"
            )
        lines.append("\nЗаписаться можно в любой момент - жмите «📅 Записаться».")
        return "\n".join(lines)

    @staticmethod
    def masters_list() -> str:
        lines = ["💈 <b>Наши мастера</b>\n"]
        for m in MASTERS.values():
            names = ", ".join(SERVICES[sid]["name"].lower() for sid in m["services"])
            lines.append(
                f"{m['emoji']} <b>{m['name']}</b> - {m['title']} · {m['experience']}\n"
                f"    <i>{m['description']}</i>\n"
                f"    🔧 {names}"
            )
        return "\n".join(lines)

    @staticmethod
    def about() -> str:
        return (
            f"ℹ️ <b>{SHOP['name']}</b>\n\n"
            f"{SHOP['about']}\n\n"
            f"📍 {SHOP['address']}\n"
            f"🕐 {SHOP['work_hours']}\n"
            f"📞 {SHOP['phone']}\n"
            f"📸 {SHOP['instagram']}\n"
            f"🗺 {SHOP['map_url']}"
        )

    @staticmethod
    def support() -> str:
        return (
            "☎️ <b>Поддержка</b>\n\n"
            f"Менеджер: <b>{SUPPORT['manager']}</b>\n"
            f"Телефон: <b>{SUPPORT['phone']}</b>\n"
            f"Отвечаем {SUPPORT['hours']}.\n\n"
            "Можно написать прямо здесь - сообщение уйдёт менеджеру."
        )

    support_ask = "✍️ Напишите вопрос одним сообщением - передадим менеджеру."
    support_sent = "✅ Сообщение отправлено! Ответим в ближайшее время."
    support_error = "😔 Не удалось отправить сообщение, попробуйте чуть позже."
