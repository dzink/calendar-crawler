#!/usr/bin/python
"""
This module scrapes a number of publicly available event listings, parses them, and
the creates Google Calendar events out of them.
"""

import argparse
import sys
import yaml
sys.path.append('./src')
sys.path.append('./src/parsers')

from CalendarFactory import CalendarFactory
from CalendarLogger import logger, addLoggerArgsToParser, buildLogger
from EventList import EventList


OPTIONS = None
FACTORY = None

def main():
    try:
        global OPTIONS # pylint: disable=global-statement
        global FACTORY # pylint: disable=global-statement
        OPTIONS = parse_arguments()
        buildLogger(OPTIONS)
        FACTORY = CalendarFactory(OPTIONS)

        source_configs = load_config('./data/sources.yml')
        secrets = load_config('./data/secrets.yml')
        calendar_configs = load_config('./data/calendars.yml')
        # Iterate through calendars in config
        for calendar_key in calendar_configs.keys():
            calendar_config = calendar_configs.get(calendar_key)

            google_calendar = FACTORY.googleCalendar(calendar_config, secrets)
            events = EventList()

            source_keys = calendar_config.get('sources', [])
            if (OPTIONS.source):
                source_keys = list(filter(lambda x: x in source_keys, OPTIONS.source))

            # Iterate through sources in calendar config
            for source_key in source_keys:
                source_config = source_configs.get(source_key)

                events = events.merge(get_events(source_key, source_config))

            for event in events:
                event.deduplicate(forceUpdateIfMatched = OPTIONS.force_update)
                if (not OPTIONS.dry_run):
                    google_calendar.syncEvent(event)
                    event.write()
                else:
                    google_calendar.dryRun(event, OPTIONS.show_skips)

    # This exception is intentionally broad and will catch anything not caught otherwise
    # and will send it to the logger
    # pylint: disable=broad-except
    except Exception:
        logger.exception("Exception occurred")

def parse_arguments():
    """Creates a parser and parses command line arguments."""
    # pylint: disable=line-too-long
    parser = argparse.ArgumentParser(description='Scrape event pages and add them to a Google calendar')
    addLoggerArgsToParser(parser)
    parser.add_argument('-l', '--local', help = 'Whether to use local cached sources instead of re-scraping html.', action = 'store_false', default = True, dest = 'remote')
    parser.add_argument('-u', '--force-update', help = 'Whether to force Google Calendar updates, even if there\'s nothing to update.', action = 'store_true', default = False)
    parser.add_argument('-d', '--dry-run', help = 'Run the parser but do not write to the calendar or database.', action = 'store_true', default = False)
    parser.add_argument('-s', '--source', help = 'Only crawl the given source(s).', action = 'append', default = None)
    parser.add_argument('--show-skips', help = 'In a dry run, ignore the skips.', action = 'store_false', default = True)

    return parser.parse_args()

def load_config(filename):
    """Loads a config file."""
    with open(filename, 'r') as file:
        config = yaml.safe_load(file)
        return config

def get_events(source_id, source_config):
    """Gets events for a given source based on the config passed in."""
    source = FACTORY.source(source_id, source_config)
    html = source.getHtml()

    parser = FACTORY.parser(source_config)
    events = parser.parse(html).events

    events = FACTORY.postTasks(events, source_config)

    return events

if __name__ == '__main__':
    main()
