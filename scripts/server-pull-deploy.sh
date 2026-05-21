#!/usr/bin/env bash
# На сервере: подтянуть git и применить настройки в Dify.
# С вашего ПК: правки → git push → на сервере: ./scripts/server-pull-deploy.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BRANCH="${DEPLOY_BRANCH:-main}"
RUN_GOLDEN="${RUN_GOLDEN:-1}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Ошибка: не git-репозиторий ($ROOT)" >&2
  exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "Ошибка: нет remote origin. Добавьте: git remote add origin <URL>" >&2
  exit 1
fi

echo "==> git fetch"
git fetch origin

echo "==> git pull origin ${BRANCH}"
git pull --ff-only origin "${BRANCH}"

echo "==> Dify: KB + prompt sync"
RUN_GOLDEN="${RUN_GOLDEN}" ./scripts/support-setup.sh

if [[ "${RUN_GOLDEN}" == "1" ]]; then
  echo "==> Golden tests"
  ./scripts/run-golden-tests.sh
fi

echo ""
echo "Деплой завершён. Dify: http://localhost (приложение Avaid Support)"
