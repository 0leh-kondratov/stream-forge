#!/usr/bin/env bash
set -euo pipefail

# 1) Куда инициализируем (можно передать как 1-й аргумент)
TF_ROOT="${1:-infra/live/dev/gke}"

# 2) Имя стейта (по окружению)
TF_STATE_NAME="${TF_STATE_NAME:-dev-gke}"

# 3) Адрес API GitLab
CI_API_V4_URL="${CI_API_V4_URL:-https://gitlab.dmz.home/api/v4}"

# 4) ID проекта (в CI приходит автоматически; локально — экспортируй сам)
: "${CI_PROJECT_ID:?CI_PROJECT_ID is required (export it locally or run in CI)}"

BACKEND_ADDR="${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/terraform/state/${TF_STATE_NAME}"

# Локально вместо CI_JOB_TOKEN задай:
#   export TF_BACKEND_USERNAME="terraform"
#   export TF_BACKEND_PASSWORD="$GL_PAT"   # твой персональный PAT (scope: api)
TF_BACKEND_USERNAME="${TF_BACKEND_USERNAME:-gitlab-ci-token}"
TF_BACKEND_PASSWORD="${TF_BACKEND_PASSWORD:-${CI_JOB_TOKEN:-}}"

if ! find "$TF_ROOT" -maxdepth 1 -name '*.tf' -print -quit | grep -q .; then
  echo "ERROR: No .tf files found in $TF_ROOT"; exit 1
fi

cd "$TF_ROOT"

terraform init \
  -backend-config=address="$BACKEND_ADDR" \
  -backend-config=lock_address="$BACKEND_ADDR/lock" \
  -backend-config=unlock_address="$BACKEND_ADDR/lock" \
  -backend-config=username="$TF_BACKEND_USERNAME" \
  -backend-config=password="$TF_BACKEND_PASSWORD" \
  -backend-config=lock_method=POST \
  -backend-config=unlock_method=DELETE \
  -backend-config=retry_wait_min=5
