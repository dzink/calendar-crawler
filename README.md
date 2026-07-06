# calendar-crawler.py - A Calendar Crawler

Scrape event pages and add them to a Google calendar

```
optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Verbose output.
  --debug               Debug output.
  --log-file LOG_FILE
  -l, --local           Whether to use local cached sources instead of re-scraping html.
  -u, --force-update    Whether to force Google Calendar updates, even if there's nothing to
                        update.
  -d, --dry-run         Run the parser but do not write to the calendar or database.
  -s SOURCE, --source SOURCE
                        Only crawl the given source(s).
  --show-skips          In a dry run, ignore the skips.

```

## Install
This app runs on Python 3.

### Requirements

Set up a virtual environment and install dependencies:

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Configuration

Copy the example config files in `data/` and fill in real values:

- `data/options.yml` (from `example-data/example.options.yml`) — Chrome binary path and other options
- `data/secrets.yml` (from `example-data/example.secrets.yml`) — Google Calendar API credentials and calendar ID. The credentials data comes straight from your Google Calendar app JSON (paste as-is, since JSON is valid YAML). The calendar ID comes from Google Calendar settings.

### Chrome

A headless Chrome or Chromium browser is required for scraping. The recommended approach is to install Google Chrome as a `.deb` package (not Snap or Flatpak, which have sandboxing issues with headless mode):

```
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
```

Then set the binary path in `data/options.yml`:

```yml
chromeBinaryLocation: '/usr/bin/google-chrome'
```

The matching chromedriver is downloaded automatically via `webdriver_manager` and cached in `~/.wdm/`.

If you prefer to manage chromedriver manually, set `chromeDriverLocation` in `data/options.yml` to the path of your chromedriver binary.

### Scheduled runs (systemd)

To run the crawler daily as a systemd user timer:

```
./install-systemd.sh
```

This installs a service and timer to `~/.config/systemd/user/` and enables the timer. The crawler will run once a day (with a 30-minute randomized delay), wait for network connectivity, and send desktop notifications on start and finish.

Useful commands:

```
systemctl --user status calendar-crawler.timer    # check timer status
journalctl --user -u calendar-crawler.service     # view logs
systemctl --user start calendar-crawler.service   # run manually
```

You can customize the schedule by editing `~/.config/systemd/user/calendar-crawler.timer`. See `example-data/example.calendar-crawler.service` and `example-data/example.calendar-crawler.timer` for reference.

## Troubleshooting

If you have trouble logging in, make sure you use the localhost domain with the port number in your google app setup.

If you were able to log in but now you can't refresh, delete the file at `.data/token.json`


# calendar-cleaner.py - An event deleter for old events.

Currently this is hardcoded to anything older than 32 days.

```
Clean old events from the calendar

optional arguments:
  -h, --help           show this help message and exit
  -v, --verbose        Verbose output.
  --debug              Debug output.
  --log-file LOG_FILE
  -d, --dry-run        Run the cleaner but do not write to the calendar or database.
```


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
