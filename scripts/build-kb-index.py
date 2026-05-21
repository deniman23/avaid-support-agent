#!/usr/bin/env python3
"""Собрать единый индекс KB для Dify: scenarios + reference + style."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "shared" / "knowledge"
INDEX = KNOWLEDGE / ".dify-index"
RULES = KNOWLEDGE / "rules"

# Справочники из legacy rules/ (пока не вынесены в reference/ вручную)
LEGACY_REFERENCE_GLOBS = [
    "маркетплейсы_список.md",
    "правила_ozon.md",
    "правила_avito.md",
    "правила_яндекс_маркет.md",
    "тарифы.md",
    "инструкция_*.md",
    "общие_правила_приложения.md",
    "БАЗА_*.md",
]


def _copy_tree(src: Path, dest_prefix: Path) -> int:
    n = 0
    if not src.is_dir():
        return 0
    for f in sorted(src.rglob("*.md")):
        rel = f.relative_to(src)
        out = dest_prefix / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, out)
        n += 1
    return n


def _copy_legacy_reference(dest: Path) -> int:
    n = 0
    for pattern in LEGACY_REFERENCE_GLOBS:
        for f in RULES.glob(pattern):
            out = dest / "reference" / f.name
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out)
            n += 1
    return n


def main() -> int:
    if INDEX.exists():
        shutil.rmtree(INDEX)
    INDEX.mkdir(parents=True)

    counts = {
        "scenarios": _copy_tree(KNOWLEDGE / "scenarios", INDEX),
        "style": _copy_tree(KNOWLEDGE / "style", INDEX),
        "reference": _copy_tree(KNOWLEDGE / "reference", INDEX),
    }
    counts["reference"] += _copy_legacy_reference(INDEX)

    total = sum(counts.values())
    print(f"KB index: {INDEX}")
    for k, v in counts.items():
        print(f"  {k}: {v} files")
    print(f"  total: {total} markdown files")
    if total == 0:
        print("ERROR: empty index", file=__import__("sys").stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
