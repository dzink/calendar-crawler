#!python3./.venv/bin/python3

import sys
sys.path.append('./src')
import paths

import argparse
from EventList import EventList
from Factory import CalendarFactory
from Pipeline import CalendarPipeline
from Config import Config
from datetime import datetime

from CalendarLogger import logger, addLoggerArgsToParser, buildLogger
from Fetcher import Fetcher

def main():
    print('Running Calendar Crawler at ' + datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
    try:
        cfg = Config()
        config = cfg.loadOptions()
        sourceConfigs = cfg.loadSources()
        calendarConfigs = cfg.loadCalendars()
        secrets = cfg.loadSecrets()
        options = parseArguments(config)
        buildLogger(options)

        factory = CalendarFactory(options, config, secrets)
        pipeline = CalendarPipeline(factory, options)

        if options.source:
            allCalendarSources = set()
            for cc in calendarConfigs.values():
                allCalendarSources.update(cc.get('sources', []))
            missing = [s for s in options.source if s not in allCalendarSources]
            if missing:
                print('Warning: source(s) not found in any calendar: %s' % ', '.join(missing))
                print('Add them to calendars.yml or check the source name.')
                return

        for calendarKey in calendarConfigs:
            calendarConfig = calendarConfigs.get(calendarKey)
            events = EventList()

            sourceKeys = calendarConfig.get('sources', [])
            if options.source:
                sourceKeys = [k for k in sourceKeys if k in options.source]

            for sourceKey in sourceKeys:
                events = events.merge(pipeline.getEvents(sourceKey, sourceConfigs.get(sourceKey)))

            if options.after:
                events = EventList([e for e in events if e.startToString()[:10] >= options.after])

            inserted, updated, skipped = pipeline.sync(events, calendarKey)

            with open('./data/current.log') as f:
                errors = sum(1 for line in f if line.strip())
            print('Done. %d inserted, %d updated, %d skipped, %d errors.' % (inserted, updated, skipped, errors))

    except Exception as e:
        logger.exception("Exception occurred")
    finally:
        Fetcher.quitDriver()

def parseArguments(config):
    parser = argparse.ArgumentParser(description='Scrape event pages and add them to a Google calendar')
    addLoggerArgsToParser(parser, config.get('logging', {}))
    parser.add_argument('-l', '--local', help='Whether to use local cached sources instead of re-scraping html.', action='store_false', default=True, dest='remote')
    parser.add_argument('-u', '--force-update', help='Whether to force Google Calendar updates, even if there\'s nothing to update.', action='store_true', default=config.get('forceUpdate', False))
    parser.add_argument('-d', '--dry-run', help='Run the parser but do not write to the calendar or database.', action='store_true', default=False)
    parser.add_argument('-s', '--source', help='Only crawl the given source(s).', action='append', default=None)
    parser.add_argument('-a', '--after', help='Only include events starting on or after this date (YYYY-MM-DD).', default=None)
    parser.add_argument('-n', '--limit', help='Maximum number of events to add or update.', type=int, default=None)
    parser.add_argument('--show-skips', help='In a dry run, ignore the skips.', action='store_false', default=True)
    return parser.parse_args()

if __name__ == '__main__':
    main()
