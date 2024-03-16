#!/usr/bin/python

import sys
sys.path.append('./src')
sys.path.append('./src/parsers')

import yaml
import argparse
from EventList import EventList
from CalendarFactory import CalendarFactory

from CalendarLogger import logger, addLoggerArgsToParser, buildLogger

options = None
factory = None

def main():
    try:
        global options
        global factory
        config = loadConfig('./data/options.yml')
        sourceConfigs = loadConfig('./data/sources.yml')
        calendarConfigs = loadConfig('./data/calendars.yml')
        secrets = loadConfig('./data/secrets.yml')
        options = parseArguments(config)
        buildLogger(options)
        factory = CalendarFactory(options, config)

        # Iterate through calendars in config
        for calendarKey in calendarConfigs.keys():
            calendarConfig = calendarConfigs.get(calendarKey)

            googleCalendar = factory.googleCalendar(calendarConfig, secrets)
            events = EventList()

            sourceKeys = calendarConfig.get('sources', [])
            if (options.source):
                sourceKeys = list(filter(lambda x: x in sourceKeys, options.source))

            # Iterate through sources in calendar config
            for sourceKey in sourceKeys:
                sourceConfig = sourceConfigs.get(sourceKey)

                events = events.merge(getEvents(sourceKey, sourceConfig))

            for event in events:
                event.deduplicate(forceUpdateIfMatched = options.force_update)
                if (not options.dry_run):
                    googleCalendar.syncEvent(event)
                    event.write()
                else:
                    googleCalendar.dryRun(event, options.show_skips)

    except Exception as e:
        logger.exception("Exception occurred")

def parseArguments(config):
    parser = argparse.ArgumentParser(description='Scrape event pages and add them to a Google calendar')
    addLoggerArgsToParser(parser, config.get('logging', {}))
    parser.add_argument('-l', '--local', help = 'Whether to use local cached sources instead of re-scraping html.', action = 'store_false', default = True, dest = 'remote')
    parser.add_argument('-u', '--force-update', help = 'Whether to force Google Calendar updates, even if there\'s nothing to update.', action = 'store_true', default = config.get('forceUpdate', False))
    parser.add_argument('-d', '--dry-run', help = 'Run the parser but do not write to the calendar or database.', action = 'store_true', default = False)
    parser.add_argument('-s', '--source', help = 'Only crawl the given source(s).', action = 'append', default = None)
    parser.add_argument('--show-skips', help = 'In a dry run, ignore the skips.', action = 'store_false', default = True)

    return parser.parse_args()

def loadConfig(filename):
    with open(filename, 'r') as file:
        config = yaml.safe_load(file)
        return config

def getEvents(sourceId, sourceConfig):
    try:
        source = factory.source(sourceId, sourceConfig)
        html = source.getHtml()

        parser = factory.parser(sourceId, sourceConfig)
        events = parser.parse(html).events

        events = factory.postTasks(events, sourceConfig)

        return events

    except Exception as e:
        logger.exception("Exception occurred in source " + sourceId)
        logger.exception(e)
        return EventList()

if __name__ == '__main__':
    main()
