# A Calendar Scraper

## Setup
You'll at least want the BeautifulSoup and tinyDb python modules. Perhaps more.

You'll need your Google Calendar credentials file, saved in `./data/credentials.json`

You'll want the id of a calendar, saved in `./data/calendarid.text`. It should look something like `[long string of text]@group.calendar.google.com`

## Troubleshooting

If you have trouble logging in, make sure you use the localhost domain with the port number in your google app setup.

If you were able to log in but now you can't, delete the file at `.data/token.json`
