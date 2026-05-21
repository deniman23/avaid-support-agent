#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Создайте .env из .env.example и задайте DATABASE_URL на prod."
  exit 1
fi
# shellcheck disable=SC1091
source .env

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL не задан в .env"
  exit 1
fi

echo "==> Apply role support_writer on prod (once, as superuser):"
echo "    psql \"\$ADMIN_URL\" -f shared/db/init-support-writer.sql"
echo "    (при необходимости замените имя БД в файле)"
echo ""

echo "==> Start db-api (prod compose)"
docker compose -f docker-compose.prod.yml up -d --build

echo "==> Wait for health"
for i in {1..20}; do
  if curl -sf http://localhost:8090/health | grep -q '"database":"up"'; then
    curl -s http://localhost:8090/health
    echo ""
    echo "OK: db-api подключён к prod."
    exit 0
  fi
  sleep 2
done

echo "FAIL: health check. Проверьте DATABASE_URL, firewall, GRANT для support_writer."
curl -s http://localhost:8090/health || true
exit 1
