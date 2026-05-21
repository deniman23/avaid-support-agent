import re
from typing import Any

DENY_FIELDS = frozenset(
    {
        "password",
        "api_key",
        "access_token",
        "remember_token",
        "raw",
        "payload",
        "callback_payload",
        "telegram_bot_token",
        "telegram_webhook_secret",
        "metadata",
        "data",
        "address",
        "customer",
        "items",
        "subsidies",
        "tochka_consumer_id",
        "tochka_subscription_operation_id",
    }
)

OUTPUT_DENY_PATTERNS = [
    re.compile(r"api[_-]?key", re.I),
    re.compile(r"BEGIN\s+PRIVATE\s+KEY", re.I),
    re.compile(r"CREATE\s+TABLE", re.I),
    re.compile(r"SELECT\s+\*", re.I),
]


def pick(row: dict[str, Any], allowed: list[str]) -> dict[str, Any]:
    return {k: row[k] for k in allowed if k in row and k not in DENY_FIELDS}


def redact_log_email(email: str) -> str:
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        return f"*@{domain}"
    return f"{local[0]}***@{domain}"


def response_safe(text: str) -> bool:
    return not any(p.search(text) for p in OUTPUT_DENY_PATTERNS)
