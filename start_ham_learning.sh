#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8788}"
HOST="${2:-127.0.0.1}"

cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install -q -r requirements.txt

if [[ ! -f "data/pools/element2.json" || ! -f "data/pools/element3.json" || ! -f "data/pools/element4.json" ]]; then
  .venv/bin/python ham_practice.py update-pools
fi

echo "Starting Ham Learning Studio on http://${HOST}:${PORT}"
exec .venv/bin/python ham_learning.py web --host "$HOST" --port "$PORT"
