#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

: "${APP_DIR:?APP_DIR is not set}"

cd "${APP_DIR}"

echo "Applying migrations"
alembic upgrade head

echo "Starting daemon"
exec python3 main.py
