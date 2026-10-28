#!/usr/bin/env bash
set -euo pipefail

SERVICE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ -n "${ML_PYTHON:-}" ]]; then
  PYTHON="$ML_PYTHON"
elif [[ -x "$SERVICE_DIR/.venv/bin/python" ]]; then
  PYTHON="$SERVICE_DIR/.venv/bin/python"
elif [[ -x "$HOME/dev/pneumacare-ml-services/Env/bin/python" ]]; then
  PYTHON="$HOME/dev/pneumacare-ml-services/Env/bin/python"
else
  echo "Python environment tidak ditemukan." >&2
  echo "Set ML_PYTHON=/path/to/python, atau buat venv lokal:" >&2
  echo "  /usr/bin/python3 -m venv $SERVICE_DIR/.venv" >&2
  echo "  $SERVICE_DIR/.venv/bin/pip install --no-cache-dir -r $SERVICE_DIR/requirements.txt" >&2
  exit 1
fi

cd "$SERVICE_DIR"
exec "$PYTHON" main.py
