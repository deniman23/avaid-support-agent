#!/usr/bin/env bash
set -euo pipefail
API_KEY="${SUPPORT_API_KEY:-change-me-local-dev-key}"
BASE="${DB_API_URL:-http://localhost:8090}"
EMAIL="${TEST_EMAIL:-support@test.local}"
H=(-H "X-Support-Api-Key: $API_KEY" -H "X-Dify-User-Email: $EMAIL")

echo "health"; curl -sf "$BASE/health"
echo ""
echo "shops"; curl -sf "${H[@]}" "$BASE/support/shops" | python3 -m json.tool
echo "stock/issues"; curl -sf "${H[@]}" "$BASE/support/stock/issues" | python3 -c "import sys,json; d=json.load(sys.stdin); print('count',d['count'])"
echo "billing"; curl -sf "${H[@]}" "$BASE/support/billing/status" | python3 -m json.tool
echo "sync error"; curl -sf "${H[@]}" "$BASE/support/sync/last-error" | python3 -m json.tool
echo "403 other email"; test "$(curl -s -o /dev/null -w '%{http_code}' "${H[@]}" "$BASE/support/users/lookup?email=other@test.com")" = "403"
echo "no api_key in shops"; ! curl -sf "${H[@]}" "$BASE/support/shops" | grep -qi api_key
echo "ALL OK"
