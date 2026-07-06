#!/usr/bin/env bash
#
# cc — Calendar Crawler CLI wrapper
#
# Usage: ./cc <command> [options]
#
# Commands:
#   crawl       Scrape event pages and sync to database
#   clean       Delete events matching criteria
#   export      Build HTML agenda and ICS files
#   sync        Sync pending events to calendar providers
#   find        Search events in the database
#   migrate     Run calendar-items migration
#   watch-dev   Watch html-template/ and rebuild on changes
#   push-dist   Export, commit, and push dist/prod to origin
#   install     Install systemd user service and timer
#   update-driver  Update chromedriver to match installed Chrome
#   nightly     Run full nightly: crawl, sync, export, push
#   test        Verify the environment is set up correctly
#
# All additional arguments are passed through to the script.

set -euo pipefail
cd "$(dirname "$0")"

PYTHON=".venv/bin/python3"

if [ $# -lt 1 ]; then
    sed -n '3,/^$/{ s/^# \?//; p }' "$0"
    exit 1
fi

command="$1"
shift

case "$command" in
    crawl)    exec "$PYTHON" scripts/calendar-crawler.py "$@" ;;
    clean)    exec "$PYTHON" scripts/calendar-cleaner.py "$@" ;;
    export)   exec "$PYTHON" scripts/html-export.py "$@" ;;
    sync)     exec "$PYTHON" scripts/provider-export.py "$@" ;;
    find)     exec "$PYTHON" scripts/event-finder.py "$@" ;;
    migrate)  exec "$PYTHON" scripts/migrate-calendar-items.py "$@" ;;
    watch-dev)      exec bash scripts/html-dev-watch.sh "$@" ;;
    push-dist)      exec bash scripts/html-push-dist.sh "$@" ;;
    install)        exec bash scripts/install-systemd.sh "$@" ;;
    update-driver)  exec bash scripts/update-chromedriver.sh "$@" ;;
    nightly)        exec bash scripts/nightly.sh "$@" ;;
    test)           exec "$PYTHON" scripts/test-env.py "$@" ;;
    *)
        echo "Unknown command: $command"
        echo "Run ./cc with no arguments to see available commands."
        exit 1
        ;;
esac
