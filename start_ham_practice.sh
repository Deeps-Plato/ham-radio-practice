#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8787}"
HOST="${2:-127.0.0.1}"

cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

if [[ ! -f "data/pools/element2.json" || ! -f "data/pools/element3.json" || ! -f "data/pools/element4.json" ]]; then
  .venv/bin/pip install -q -r requirements.txt
  .venv/bin/python ham_practice.py update-pools
fi

echo "Starting Ham Practice on http://${HOST}:${PORT}"
exec .venv/bin/python ham_practice.py web --host "$HOST" --port "$PORT"
