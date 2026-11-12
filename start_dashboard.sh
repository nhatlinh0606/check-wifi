#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-8000}"

echo "=========================================================="
echo " Starting TP-Link Router Discovery & Recovery Dashboard"
echo " Web UI: http://$HOST:$PORT"
echo " API Docs: http://$HOST:$PORT/docs"
echo "=========================================================="

python3 -m backend.main
