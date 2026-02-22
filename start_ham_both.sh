#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRACTICE_PORT="${1:-8787}"
LEARNING_PORT="${2:-8788}"
HOST="${3:-127.0.0.1}"

cd "$ROOT_DIR"

if [[ "$PRACTICE_PORT" == "$LEARNING_PORT" ]]; then
  echo "Ports must be different. Got practice=${PRACTICE_PORT}, learning=${LEARNING_PORT}."
  exit 1
fi

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install -q -r requirements.txt

if [[ ! -f "data/pools/element2.json" || ! -f "data/pools/element3.json" || ! -f "data/pools/element4.json" ]]; then
  .venv/bin/python ham_practice.py update-pools
fi

check_port_free() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    if lsof -iTCP:"${port}" -sTCP:LISTEN -n -P >/dev/null 2>&1; then
      echo "Port ${port} is already in use. Pick a different port or stop the running service."
      exit 1
    fi
  fi
}

check_port_free "$PRACTICE_PORT"
check_port_free "$LEARNING_PORT"

echo "Starting Ham Practice on http://${HOST}:${PRACTICE_PORT}"
.venv/bin/python ham_practice.py web --host "$HOST" --port "$PRACTICE_PORT" &
practice_pid=$!

echo "Starting Ham Learning Studio on http://${HOST}:${LEARNING_PORT}"
.venv/bin/python ham_learning.py web --host "$HOST" --port "$LEARNING_PORT" &
learning_pid=$!

cleanup() {
  kill "$practice_pid" "$learning_pid" 2>/dev/null || true
  wait "$practice_pid" "$learning_pid" 2>/dev/null || true
}

trap cleanup INT TERM EXIT

echo
echo "Both servers are running:"
echo "  Practice: http://${HOST}:${PRACTICE_PORT}"
echo "  Learning: http://${HOST}:${LEARNING_PORT}"
echo "Press Ctrl+C to stop both."

set +e
wait -n "$practice_pid" "$learning_pid"
exit_code=$?
set -e

echo "One server stopped. Shutting down the other."
cleanup
exit "$exit_code"
