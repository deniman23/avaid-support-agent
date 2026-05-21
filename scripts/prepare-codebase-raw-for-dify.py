#!/usr/bin/env python3
"""Скопировать Go-исходники в плоский каталог для индекса Dify (без domain-*.md)."""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODEBASE = ROOT / "shared" / "codebase" / "avaid_main-dev"
OUT = ROOT / "shared" / "knowledge" / "codebase-raw"
OUT_BILLING = ROOT / "shared" / "knowledge" / "codebase-billing"
GO_ROOT = CODEBASE / "backend-go"
BILLING_DATASET_NAME = "Avaid Billing"

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

SKIP_DIRS = {".git", "vendor", "node_modules", ".idea", "bin", "dist", "testdata"}
MAX_FILE_BYTES = 80_000


def has_secret(text: str) -> bool:
    return any(p.search(text) for p in SECRET_PATTERNS)


def read_safe(path: Path, max_chars: int = 8000) -> str | None:
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except OSError:
        return None
    return None if has_secret(text) else text


def safe_flat_name(src: Path, base: Path) -> str:
    rel = src.relative_to(base)
    return str(rel).replace("/", "__").replace("\\", "__")


def extract_tariff_catalog_from_go() -> str | None:
    """Снимок тарифов из Go (billing.go) — не ручной markdown."""
    billing = CODEBASE / "backend-go" / "internal" / "api" / "billing.go"
    text = read_safe(billing, 20000)
    if not text:
        return None
    lines = [
        "# Тарифы Avaid (из исходника billing.go, package api)",
        "",
        "Ключевые слова для поиска: тариф, тарифы, виды тарифов, подписка, планы, billing,",
        "tariff_plans, База, Про, Макс, Мини, Demo, цена, лимит магазинов.",
        "",
        "Источник: константы и map tariffNames / tariffStoreLimits в backend-go.",
        "Актуальные цены в проде также в БД `tariff_plans` (см. PublicBillingTariffs).",
        "",
    ]
    for m in re.finditer(r'Tariff(\w+)ID\s*=\s*"([^"]+)"', text):
        lines.append(f"- ID **{m.group(1)}**: `{m.group(2)}`")
    names_block = re.search(r"var tariffNames = map\[string\]string\{([^}]+)\}", text, re.S)
    const_label: dict[str, str] = {}
    if names_block:
        lines.append("")
        lines.append("## Виды тарифов (названия в продукте)")
        for m in re.finditer(r"Tariff(\w+)ID:\s*\"([^\"]+)\"", names_block.group(1)):
            const_label[m.group(1)] = m.group(2)
            lines.append(f"- **{m.group(2)}**")
    limits_block = re.search(r"var tariffStoreLimits = map\[string\]int\{([^}]+)\}", text, re.S)
    if limits_block:
        lines.append("")
        lines.append("## Лимит магазинов")
        for m in re.finditer(r"Tariff(\w+)ID:\s*(\d+)", limits_block.group(1)):
            label = const_label.get(m.group(1), m.group(1))
            lines.append(f"- **{label}**: до {m.group(2)} магазинов")
    pub = read_safe(CODEBASE / "backend-go" / "internal" / "api" / "billing_public.go", 8000)
    if pub:
        for m in re.finditer(r"^//\s*(.+)$", pub, re.M):
            if "тариф" in m.group(1).lower() or "tariff" in m.group(1).lower():
                lines.append(f"- {m.group(1)}")
    return "\n".join(lines)


def main() -> int:
    if not GO_ROOT.is_dir():
        print(f"Missing {GO_ROOT}", file=sys.stderr)
        return 1

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    n_ok = n_skip = 0
    for go in sorted(GO_ROOT.rglob("*.go")):
        if go.name.endswith("_test.go"):
            continue
        if any(p in SKIP_DIRS for p in go.parts):
            continue
        try:
            data = go.read_bytes()
        except OSError:
            n_skip += 1
            continue
        if len(data) > MAX_FILE_BYTES:
            data = data[:MAX_FILE_BYTES]
        text = data.decode("utf-8", errors="ignore")
        if has_secret(text):
            n_skip += 1
            continue

        header = f"// path: {go.relative_to(CODEBASE)}\n// package context for Avaid support agent\n\n"
        # Dify upload не принимает .go — храним как .txt, внутри исходник Go
        out_name = safe_flat_name(go, GO_ROOT) + ".txt"
        (OUT / out_name).write_text(header + text, encoding="utf-8")
        n_ok += 1

    catalog = extract_tariff_catalog_from_go()
    if catalog:
        (OUT / "billing__tariffs_from_code.txt").write_text(catalog, encoding="utf-8")
        n_ok += 1
        print("  + billing__tariffs_from_code.txt (from Go)")

    print(f"Prepared {n_ok} Go files -> {OUT}")

    # Узкий индекс для вопросов про тарифы (лучше попадает в retrieval, чем 107 файлов)
    if OUT_BILLING.exists():
        shutil.rmtree(OUT_BILLING)
    OUT_BILLING.mkdir(parents=True)
    n_bill = 0
    for f in OUT.glob("*.txt"):
        low = f.name.lower()
        if "billing" in low or "tariff" in low or "billingaccess" in low:
            shutil.copy2(f, OUT_BILLING / f.name)
            n_bill += 1
    print(f"  billing subset: {n_bill} files -> {OUT_BILLING}")

    if n_skip:
        print(f"  skipped: {n_skip}")
    return 0 if n_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
