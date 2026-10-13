"""Minimal i18n layer (Russian + English) with runtime switching.

Creator: PastyNew
"""

from __future__ import annotations

RU = "ru"
EN = "en"

STRINGS: dict[str, dict[str, str]] = {
    RU: {
        "app.title": "Генератор паролей",
        "app.tagline": "PastyNew",
        "action.generate": "Сгенерировать",
        "action.copy": "Копировать",
        "action.copied": "Скопировано",
        "action.copy_all": "Копировать всё",
        "action.export": "Экспорт",
        "action.clear": "Очистить",
        "action.delete": "Удалить",
        "action.close": "Закрыть",
        "action.minimize": "Свернуть",
        "action.reveal": "Показать пароль",
        "action.hide": "Скрыть пароль",
        "action.favorite_add": "В избранное",
        "action.favorite_remove": "Убрать из избранного",
        "option.length": "Длина пароля",
        "option.amount": "Количество паролей",
        "option.digits": "Цифры (0-9)",
        "option.uppercase": "Заглавные буквы (A-Z)",
        "option.lowercase": "Строчные буквы (a-z)",
        "option.symbols": "Специальные символы (!@# и т.д.)",
        "option.warning": "Выберите хотя бы один набор символов",
        "strength.title": "Оценка стойкости",
        "strength.bits": "{bits} бит",
        "strength.crack": "взлом: {time}",
        "strength.critical": "Очень слабый",
        "strength.weak": "Слабый",
        "strength.fair": "Средний",
        "strength.strong": "Надёжный",
        "strength.very_strong": "Очень надёжный",
        "strength.excellent": "Максимальный",
        "time.instant": "мгновенно",
        "time.seconds": "{n} сек",
        "time.minutes": "{n} мин",
        "time.hours": "{n} ч",
        "time.days": "{n} дн",
        "time.years": "{n} лет",
        "time.centuries": "века",
        "time.millennia": "тысячелетия",
        "time.forever": "миллиарды лет",
        "list.title": "Сгенерированные пароли ({n})",
        "history.title": "История",
        "history.favorites": "Избранное",
        "history.empty": "Пока пусто. Сгенерируйте пароль — он появится здесь.",
        "history.empty_fav": "Нет избранных паролей. Нажмите ☆ рядом с паролем в истории.",
        "history.cleared": "История очищена",
        "history.cleared_fav": "Избранное очищено",
        "history.exported": "Сохранено: {path}",
        "history.count": "Всего: {n}",
        "footer.made_by": "Создатель генератора паролей — PastyNew",
        "footer.offline": "Работает офлайн · v{version}",
        "toast.exported": "Файл сохранён",
        "toast.favorite_added": "Добавлено в избранное",
        "toast.favorite_removed": "Удалено из избранного",
        "toast.deleted": "Пароль удалён",
    },
    EN: {
        "app.title": "Password Generator",
        "app.tagline": "PastyNew",
        "action.generate": "Generate",
        "action.copy": "Copy",
        "action.copied": "Copied",
        "action.copy_all": "Copy all",
        "action.export": "Export",
        "action.clear": "Clear",
        "action.delete": "Delete",
        "action.close": "Close",
        "action.minimize": "Minimize",
        "action.reveal": "Show password",
        "action.hide": "Hide password",
        "action.favorite_add": "Add to favourites",
        "action.favorite_remove": "Remove from favourites",
        "option.length": "Password length",
        "option.amount": "Number of passwords",
        "option.digits": "Digits (0-9)",
        "option.uppercase": "Uppercase letters (A-Z)",
        "option.lowercase": "Lowercase letters (a-z)",
        "option.symbols": "Special characters (!@# etc.)",
        "option.warning": "Select at least one character set",
        "strength.title": "Strength estimate",
        "strength.bits": "{bits} bits",
        "strength.crack": "crack: {time}",
        "strength.critical": "Very weak",
        "strength.weak": "Weak",
        "strength.fair": "Fair",
        "strength.strong": "Strong",
        "strength.very_strong": "Very strong",
        "strength.excellent": "Maximum",
        "time.instant": "instantly",
        "time.seconds": "{n} sec",
        "time.minutes": "{n} min",
        "time.hours": "{n} h",
        "time.days": "{n} days",
        "time.years": "{n} years",
        "time.centuries": "centuries",
        "time.millennia": "millennia",
        "time.forever": "billions of years",
        "list.title": "Generated passwords ({n})",
        "history.title": "History",
        "history.favorites": "Favourites",
        "history.empty": "Nothing here yet. Generate a password and it will show up.",
        "history.empty_fav": "No favourites yet. Press ☆ next to a password in history.",
        "history.cleared": "History cleared",
        "history.cleared_fav": "Favourites cleared",
        "history.exported": "Saved: {path}",
        "history.count": "Total: {n}",
        "footer.made_by": "Creator of the password generator — PastyNew",
        "footer.offline": "Runs offline · v{version}",
        "toast.exported": "File saved",
        "toast.favorite_added": "Added to favourites",
        "toast.favorite_removed": "Removed from favourites",
        "toast.deleted": "Password deleted",
    },
}


class Translator:
    """Holds the active language and formats strings with ``{}`` fields."""

    def __init__(self, language: str = RU) -> None:
        self.language = language if language in STRINGS else RU

    def set_language(self, language: str) -> None:
        if language in STRINGS:
            self.language = language

    def toggle(self) -> str:
        self.language = EN if self.language == RU else RU
        return self.language

    def get(self, key: str, **fields: object) -> str:
        table = STRINGS[self.language]
        text = table.get(key) or STRINGS[RU].get(key, key)
        if fields:
            try:
                return text.format(**fields)
            except (KeyError, IndexError, ValueError):
                return text
        return text


def format_duration(seconds: float, tr: Translator) -> str:
    """Human readable crack time: seconds -> 'века' / 'centuries'."""
    if seconds <= 1:
        return tr.get("time.instant")
    if seconds < 60:
        return tr.get("time.seconds", n=int(seconds))
    if seconds < 3600:
        return tr.get("time.minutes", n=int(seconds // 60))
    if seconds < 86400:
        return tr.get("time.hours", n=int(seconds // 3600))
    if seconds < 86400 * 365:
        return tr.get("time.days", n=int(seconds // 86400))
    years = seconds / (86400 * 365.25)
    if years < 100:
        return tr.get("time.years", n=int(years))
    if years < 100_000:
        return tr.get("time.centuries", n=int(years / 100))
    if years < 1_000_000_000:
        return tr.get("time.millennia", n=int(years / 1000))
    return tr.get("time.forever")