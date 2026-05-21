#!/usr/bin/env python3
"""Прогон golden-тестов через Dify Chat API (blocking)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests" / "support-golden.json"
if not GOLDEN.is_file():
    GOLDEN = ROOT / "tests" / "support-golden.yaml"
APP_ID = os.environ.get("DIFY_APP_ID", "5005f9d9-2d02-4422-b7e2-bdf5a518414b")
BASE = os.environ.get("DIFY_API_URL", "http://localhost/v1").rstrip("/")


def load_cases() -> list[dict]:
    text = GOLDEN.read_text(encoding="utf-8")
    if GOLDEN.suffix == ".json":
        data = json.loads(text)
    else:
        try:
            import yaml
        except ImportError:
            print("Install PyYAML or use support-golden.json", file=sys.stderr)
            sys.exit(1)
        data = yaml.safe_load(text)
    defaults = data.get("defaults") or {}
    cases = []
    for c in data.get("cases") or []:
        merged = {**defaults, **c}
        cases.append(merged)
    return cases


def get_api_key() -> str:
    key = os.environ.get("DIFY_APP_API_KEY", "").strip()
    if key:
        return key
    sql = f"SELECT token FROM api_tokens WHERE app_id='{APP_ID}' ORDER BY created_at DESC LIMIT 1;"
    for cmd in (
        ["sg", "docker", "-c", f"docker exec docker-db_postgres-1 psql -U postgres -d dify -tAc \"{sql}\""],
        ["docker", "exec", "docker-db_postgres-1", "psql", "-U", "postgres", "-d", "dify", "-tAc", sql],
    ):
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        if out:
            return out
    # create token via Dify API container
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "dify-ensure-app-token-docker.py"
    if script.is_file():
        for cmd in (
            ["sg", "docker", "-c", f"docker cp {script} docker-api-1:/tmp/dify-ensure-app-token-docker.py && docker exec docker-api-1 python -u /tmp/dify-ensure-app-token-docker.py"],
            ["docker", "cp", str(script), "docker-api-1:/tmp/dify-ensure-app-token-docker.py"],
        ):
            try:
                if "cp" in cmd and len(cmd) == 4:
                    subprocess.check_call(cmd, stderr=subprocess.DEVNULL)
                    continue
                out = subprocess.check_output(
                    ["sg", "docker", "-c", "docker exec docker-api-1 python -u /tmp/dify-ensure-app-token-docker.py"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                ).strip()
                if out:
                    return out
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
    print("Set DIFY_APP_API_KEY or run support-setup / dify-ensure-app-token-docker.py", file=sys.stderr)
    sys.exit(1)


def chat(api_key: str, question: str, user: str) -> str:
    payload = {
        "inputs": {"user_email": ""},
        "query": question,
        "response_mode": "blocking",
        "user": user,
    }
    req = urllib.request.Request(
        f"{BASE}/chat-messages",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=int(os.environ.get("GOLDEN_TIMEOUT", "180"))) as resp:
        body = json.loads(resp.read().decode())
    return (body.get("answer") or "").strip()


def main() -> int:
    cases = load_cases()
    only = os.environ.get("GOLDEN_ONLY", "").strip()
    if only:
        ids = {x.strip() for x in only.split(",") if x.strip()}
        cases = [c for c in cases if c.get("id") in ids]
        if not cases:
            print(f"No cases for GOLDEN_ONLY={only!r}", file=sys.stderr)
            return 1
    api_key = get_api_key()
    print(f"Golden tests: {len(cases)} cases, app={APP_ID}")

    failed = 0
    for case in cases:
        cid = case["id"]
        q = case["question"]
        print(f"\n--- {cid}")
        try:
            answer = chat(api_key, q, case.get("user", "golden-test"))
        except urllib.error.HTTPError as e:
            print(f"  FAIL HTTP {e.code}: {e.read().decode()[:500]}")
            failed += 1
            continue
        except Exception as e:
            print(f"  FAIL {e}")
            failed += 1
            continue

        low = answer.lower()
        ok = True
        for phrase in case.get("must_contain") or []:
            if phrase.lower() not in low:
                print(f"  FAIL missing: {phrase!r}")
                ok = False
        for phrase in case.get("must_not_contain") or []:
            if phrase.lower() in low:
                print(f"  FAIL forbidden: {phrase!r}")
                ok = False

        if ok:
            print(f"  OK ({len(answer)} chars)")
        else:
            print(f"  Answer snippet: {answer[:400]}...")
            failed += 1

    print(f"\n==> {len(cases) - failed}/{len(cases)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
