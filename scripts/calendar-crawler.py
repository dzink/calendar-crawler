#!python3./.venv/bin/python3

import sys
sys.path.append('./src')
import paths

import yaml
import argparse
from EventList import EventList
from Factory import CalendarFactory
from Pipeline import CalendarPipeline
from datetime import datetime

from CalendarLogger import logger, addLoggerArgsToParser, buildLogger
from Fetcher import Fetcher

def main():
    print('Running Calendar Crawler at ' + datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
    try:
        config = loadConfig('./data/options.yml')
        sourceConfigs = loadConfig('./data/sources.yml')
        calendarConfigs = loadConfig('./data/calendars.yml')
        secrets = loadConfig('./data/secrets.yml')
        options = parseArguments(config)
        buildLogger(options)

        factory = CalendarFactory(options, config, secrets)
        pipeline = CalendarPipeline(factory, options)

        for calendarKey in calendarConfigs:
            calendarConfig = calendarConfigs.get(calendarKey)
            events = EventList()

            sourceKeys = calendarConfig.get('sources', [])
            if options.source:
                sourceKeys = [k for k in sourceKeys if k in options.source]

            for sourceKey in sourceKeys:
                events = events.merge(pipeline.getEvents(sourceKey, sourceConfigs.get(sourceKey)))

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
    parser.add_argument('--show-skips', help='In a dry run, ignore the skips.', action='store_false', default=True)
    return parser.parse_args()

def loadConfig(filename):
    try:
        with open(filename, 'r') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        return {}

if __name__ == '__main__':
    main()
