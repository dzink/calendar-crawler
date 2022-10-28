# calendar-crawler.py - A Calendar Crawler

Scrape event pages and add them to a Google calendar

```
optional arguments:
  -h, --help           show this help message and exit
  -v, --verbose        Verbose output.
  --log-file LOG_FILE
  -l, --local          Whether to use local cached sources instead of re-scraping html.
  -u, --force-update   Whether to force Google Calendar updates, even if there's nothing to update.
  -d, --dry-run        Run the parser but do not write to the calendar or database.
```

## Install
This app runs on python 3.

You'll at least want the BeautifulSoup and tinyDb python modules. Perhaps more.

In `./data/secrets.yml`, you will need a file that looks like `./data/example.secrets.yml`, only with the real data. The credentials data comes straight from your Google Calendar app json, you can paste it in as-is since json is valid yml. The calendar id comes from the calendar settings.

## Troubleshooting

If you have trouble logging in, make sure you use the localhost domain with the port number in your google app setup.

If you were able to log in but now you can't, delete the file at `.data/token.json`


# event-finder.py - An event finder

This tool is mostly for debugging.

Scrape event pages and add them to a Google calendar

```
optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Verbose output.
  --debug               Debug output.
  --log-file LOG_FILE
  -l LOCATION, --location LOCATION
                        Search by location/venue
  -s SUMMARY, --summary SUMMARY
                        Search by title/artist/etc
  -o SOURCE, --source SOURCE
                        Search by import source
  -d DATE, --date DATE  Search by date in the format YYYY-MM-DD
  -a AFTER, --after AFTER
                        Search after a date in the format YYYY-MM-DD
  -t, --today           Search for events today
  -u, --upcoming        Search for upcoming events
  -p, --past            Search for past events
  -e DESCRIPTION, --description DESCRIPTION
                        Search by event descriptions
  -c, --count           Return the count only
```
