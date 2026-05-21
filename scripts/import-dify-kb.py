#!/usr/bin/env python3
"""Upload knowledge files to Dify datasets via API (optional automation)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATASETS = {
    "Avaid Rules": ROOT / "shared" / "knowledge" / "rules",
    "Avaid Codebase": ROOT / "shared" / "knowledge" / "codebase",
}


def main() -> int:
    base = os.environ.get("DIFY_API_URL", "http://localhost/console/api")
    key = os.environ.get("DIFY_API_KEY", "")
    if not key:
        print("Set DIFY_API_KEY and optionally DIFY_API_URL", file=sys.stderr)
        print("Manual: Studio → Knowledge → Create dataset → upload folders:", file=sys.stderr)
        for name, path in DATASETS.items():
            print(f"  - {name}: {path}")
        print(f"  - Avaid DB Schema: {ROOT / 'shared/docs/db-schema-for-agent.md'}")
        return 0
    print("DIFY_API_KEY set — implement dataset sync via Dify API v1 if needed.")
    print("For phase 1, manual upload of the paths above is sufficient.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
