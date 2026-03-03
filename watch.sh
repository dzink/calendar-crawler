#!/usr/bin/env bash
# watch.sh — Rebuild dev export on any file change in html-template/.
# Requires: inotify-tools (sudo apt install inotify-tools)

set -euo pipefail

DIR="$(dirname "$0")/html-template"

if ! command -v inotifywait &>/dev/null; then
  echo "inotifywait not found. Install with: sudo apt install inotify-tools"
  exit 1
fi

echo "Watching $DIR for changes..."
.venv/bin/python3 calendar-export.py --dev -v

while inotifywait -r -e modify,create "$DIR" --quiet; do
  echo "Change detected, rebuilding..."
  .venv/bin/python3 calendar-export.py --dev -v
done
