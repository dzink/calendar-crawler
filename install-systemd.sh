#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
SYSTEMD_DIR="$HOME/.config/systemd/user"

mkdir -p "$SYSTEMD_DIR"

sed "s|/path/to/calendar-crawler|$PROJECT_DIR|g" \
    "$PROJECT_DIR/data/example.calendar-crawler.service" \
    > "$SYSTEMD_DIR/calendar-crawler.service"

cp "$PROJECT_DIR/data/example.calendar-crawler.timer" \
    "$SYSTEMD_DIR/calendar-crawler.timer"

systemctl --user daemon-reload
systemctl --user enable --now calendar-crawler.timer

echo "Installed and enabled calendar-crawler timer."
echo "Check status: systemctl --user status calendar-crawler.timer"
