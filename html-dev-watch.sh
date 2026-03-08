#!/usr/bin/env bash
# watch.sh — Rebuild dev export on any file change in html-template/.
# Requires: inotify-tools (sudo apt install inotify-tools)

set -uo pipefail

DIR="$(dirname "$0")/html-template"

if ! command -v inotifywait &>/dev/null; then
  echo "inotifywait not found. Install with: sudo apt install inotify-tools"
  exit 1
fi

rebuild() {
  .venv/bin/python3 html-export.py --dev
}

echo "Watching $DIR for changes... (press Enter to rebuild manually)"
rebuild

while true; do
  # Start file watcher in background
  inotifywait -r -e modify,create "$DIR" --quiet &>/dev/null &
  INOTIFY_PID=$!
  # Block until Enter or inotifywait exits
  while kill -0 "$INOTIFY_PID" 2>/dev/null; do
    if read -t 0.5 -s 2>/dev/null; then
      kill "$INOTIFY_PID" 2>/dev/null; wait "$INOTIFY_PID" 2>/dev/null
      echo "Manual rebuild..."
      rebuild
      continue 2
    fi
  done
  wait "$INOTIFY_PID" 2>/dev/null
  echo "Change detected, rebuilding..."
  rebuild
done
