#!/usr/bin/env bash
cd "$(dirname "$0")"

notify-send "Calendar Crawler" "Starting crawl..."

logfile=$(mktemp)
nice -n 19 .venv/bin/python calendar-crawler.py "$@" 2>&1 | tee "$logfile"
exit_code=${PIPESTATUS[0]}

summary=$(grep "^Done\." "$logfile")

if [ -s ./data/current.log ]; then
    (
        action=$(notify-send "Calendar Crawler" "$summary" --action="view=View Errors")
        if [ "$action" = "view" ]; then
            zenity --text-info --filename=./data/current.log --title="Calendar Crawler - Error Log" --width=800 --height=600 2>/dev/null
        fi
    ) &
else
    notify-send "Calendar Crawler" "$summary"
fi

rm -f "$logfile"
exit $exit_code
