#!/usr/bin/env python3
"""Generate Russian markdown summaries from avaid_main-dev for Dify KB (no raw secrets)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODEBASE = ROOT / "shared" / "codebase" / "avaid_main-dev"
OUT = ROOT / "shared" / "knowledge" / "codebase"
GO_INTERNAL = CODEBASE / "backend-go" / "internal"

SECRET_PATTERNS = [
    re.compile(p, re.I)
    for p in [
        r"api[_-]?key\s*=",
        r"password\s*=",
        r"Bearer\s+[A-Za-z0-9._-]+",
        r"BEGIN\s+(RSA\s+)?PRIVATE\s+KEY",
        r"secret[_-]?key",
        r"telegram_bot_token",
    ]
]

DOMAIN_MAP = {
    "ozon": "domain-ozon.md",
    "wildberries": "domain-wildberries.md",
    "yandex": "domain-yandex.md",
    "avito": "domain-avito.md",
    "moysklad": "domain-moysklad.md",
    "ordernotify": "domain-orders.md",
    "billingaccess": "domain-billing.md",
    "telegram": "domain-telegram.md",
    "autolink": "domain-autolink.md",
    "barcode": "domain-barcodes.md",
    "taskevent": "domain-sync-errors.md",
}

SKIP_DIRS = {".git", "vendor", "node_modules", ".idea", "bin", "dist"}


def has_secret(text: str) -> bool:
    return any(p.search(text) for p in SECRET_PATTERNS)


def read_safe(path: Path, max_chars: int = 8000) -> str | None:
    if not path.is_file():
        return None
    if path.suffix in {".env", ".pem", ".key"} or ".env" in path.name:
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except OSError:
        return None
    return None if has_secret(text) else text


def extract_go_comments(text: str) -> list[str]:
    """Комментарии из Go — основной источник бизнес-смысла для агента."""
    seen: set[str] = set()
    bullets: list[str] = []
    for m in re.finditer(r"^//\s*(.+)$", text, re.M):
        line = m.group(1).strip()
        if len(line) < 12:
            continue
        if line.startswith(("nolint", "go:", "TODO", "FIXME")):
            continue
        if line in seen:
            continue
        seen.add(line)
        bullets.append(f"- {line}")
    return bullets


def extract_rule_lists(text: str) -> list[str]:
    bullets: list[str] = []
    for m in re.finditer(
        r"var\s+(\w+)\s*=\s*\[\]string\{([^}]+)\}",
        text,
        re.S,
    ):
        name, body = m.group(1), m.group(2)
        items = re.findall(r'"([^"]+)"', body)
        if items:
            bullets.append(f"- Правила `{name}`: {', '.join(items)}")
    return bullets


def extract_go_summary(pkg_dir: Path) -> list[str]:
    bullets: list[str] = []
    for go in sorted(pkg_dir.glob("*.go"))[:25]:
        if go.name.endswith("_test.go"):
            continue
        text = read_safe(go, 12000)
        if not text:
            continue
        bullets.extend(extract_go_comments(text))
        bullets.extend(extract_rule_lists(text))
    # дедуп с сохранением порядка
    seen: set[str] = set()
    out: list[str] = []
    for b in bullets:
        if b not in seen:
            seen.add(b)
            out.append(b)
    return out[:35]


def domain_doc(name: str, title: str) -> str:
    pkg = GO_INTERNAL / name
    lines = [f"# {title}", "", f"Краткое описание возможностей Avaid (ветка dev, пакет `{name}`).", ""]
    if not pkg.is_dir():
        lines.append("_Пакет не найден в архиве._")
        return "\n".join(lines)
    bullets = extract_go_summary(pkg)
    if bullets:
        lines.append("## Бизнес-логика (из комментариев и кода backend-go)")
        lines.extend(bullets)
    else:
        lines.append("_В архиве нет читаемых комментариев для этого пакета._")
    lines.extend(
        [
            "",
            "## Для агента поддержки",
            "- Переводи логику кода в **шаги в интерфейсе Avaid**.",
            "- Не цитируй имена функций пользователю.",
            "- При вопросе «как работает» — этот документ важнее коротких FAQ-сценариев.",
        ]
    )
    return "\n".join(lines)


def api_overview() -> str:
    api_dir = GO_INTERNAL / "api"
    lines = [
        "# Обзор HTTP API (Go)",
        "",
        "Справочник для агента: какие области обслуживает бэкенд (без путей и секретов).",
        "",
    ]
    if api_dir.is_dir():
        handlers = []
        for go in sorted(api_dir.glob("*.go")):
            text = read_safe(go, 12000)
            if not text:
                continue
            for m in re.finditer(r'(?:HandleFunc|GET|POST|PUT|DELETE|PATCH)\s*\(\s*"([^"]+)"', text):
                path = m.group(1)
                if "admin" in path.lower() or "debug" in path.lower():
                    continue
                handlers.append(path)
        if handlers:
            lines.append("## Публичные области (обобщённо)")
            for h in sorted(set(handlers))[:60]:
                area = h.split("/")[1] if "/" in h else h
                lines.append(f"- Раздел `{area}` — операции кабинета")
    lines.append("")
    lines.append("Клиенту не перечисляйте URL и методы — только шаги в интерфейсе.")
    return "\n".join(lines)


def features_index() -> str:
    lines = [
        "# Карта модулей Avaid (backend-go)",
        "",
        "Используйте при вопросах «что умеет» и при нехватке правил в KB Rules.",
        "",
        "| Модуль | Назначение |",
        "|--------|------------|",
        "| ozon | Ozon: товары, остатки, заказы, акции, уценка |",
        "| wildberries | Wildberries: контент, склады, заказы |",
        "| yandex | Яндекс Маркет |",
        "| avito | Avito |",
        "| moysklad | МойСклад: синхронизация, склады, заказы |",
        "| ordernotify | Уведомления о заказах (Telegram) |",
        "| billingaccess | Доступ по тарифу |",
        "| telegram | Поддержка через Telegram |",
        "| autolink | Автопривязка товаров |",
        "| barcode | Этикетки и штрихкоды |",
        "| taskevent | Фоновые задачи и ошибки синка |",
        "",
        "Legacy Laravel (`backend-laravel`) — не цитируйте как основной источник.",
    ]
    return "\n".join(lines)


def stock_prices_doc() -> str:
    return """# Остатки и цены (обобщение)

## Остатки
- На уровне магазина: рубильник синхронизации остатков (в кабинете — настройки магазина).
- На уровне товара: флаги синхронизации остатков по позиции.
- Данные МойСклад: остатки в карточке товара МС и по складам.

## Цены
- Рубильник цен на магазине.
- Синхронизация цен по товару, минимальная цена, исключение из акций (Ozon).

## Диагностика (для агента)
1. Проверить магазин активен и рубильники включены.
2. Проверить привязку товара к МойСклад.
3. Посмотреть последнюю ошибку фоновой задачи через tool.

Не называйте пользователю имена полей БД.
"""


def main() -> int:
    if not CODEBASE.is_dir():
        print(f"Missing codebase: {CODEBASE}", file=sys.stderr)
        print("Unzip avaid_main-dev.zip to shared/codebase/", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)

    docs = {
        "features-index.md": features_index(),
        "go-api-overview.md": api_overview(),
        "domain-stock-prices.md": stock_prices_doc(),
    }

    titles = {
        "ozon": "Ozon",
        "wildberries": "Wildberries",
        "yandex": "Яндекс Маркет",
        "avito": "Avito",
        "moysklad": "МойСклад",
        "ordernotify": "Заказы и уведомления",
        "billingaccess": "Тарифы и доступ",
        "telegram": "Telegram",
        "autolink": "Автопривязка",
        "barcode": "Штрихкоды и этикетки",
        "taskevent": "Ошибки синхронизации",
    }
    for pkg, fname in DOMAIN_MAP.items():
        docs[fname] = domain_doc(pkg, titles.get(pkg, pkg))

    readme = CODEBASE / "backend-go" / "README.md"
    safe = read_safe(readme)
    if safe:
        docs["backend-go-readme.md"] = "# README backend-go (выжимка)\n\n" + safe[:6000]

    for name, body in docs.items():
        if has_secret(body):
            body = "[содержимое отфильтровано: возможные секреты]"
        (OUT / name).write_text(body, encoding="utf-8")
        print("wrote", name)

    print(f"Done: {len(docs)} files -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
