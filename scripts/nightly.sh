#!/usr/bin/env bash
# nightly.sh — Crawl all sources, sync providers, export and push dist.

cd "$(dirname "$0")/.."

notify-send "Calendar Crawler" "Starting nightly run..."

logfile=$(mktemp)

run_step() {
    local label="$1"
    shift
    echo "=== $label ===" | tee -a "$logfile"
    nice -n 19 "$@" 2>&1 | tee -a "$logfile"
    local code=${PIPESTATUS[0]}
    if [ $code -ne 0 ]; then
        (
            action=$(notify-send "Calendar Crawler" "Nightly failed at: $label" --action="view=View Log")
            if [ "$action" = "view" ]; then
                zenity --text-info --filename="$logfile" --title="Calendar Crawler - Nightly Error" --width=800 --height=600 2>/dev/null
            fi
        ) &
        rm -f "$logfile"
        exit $code
    fi
}

run_step "Crawl"     ./cc crawl -v
run_step "Sync"      ./cc sync -v
run_step "Push dist" ./cc push-dist -y

notify-send "Calendar Crawler" "Nightly run complete."
rm -f "$logfile"
