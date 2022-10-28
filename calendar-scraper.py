#!/usr/bin/python

import sys
sys.path.append('./src')
sys.path.append('./src/parsers')

import yaml
import argparse
from EventList import EventList
from GoogleCalendar import GoogleCalendar
from CalendarFactory import CalendarFactory

from time import sleep
from CalendarLogger import logger, addLoggerArgsToParser, buildLogger

options = None
factory = None

def main():
    try:
        global options
        global factory
        options = parseArguments()
        buildLogger(options)
        factory = CalendarFactory(options)

        sourceConfigs = loadConfig('./sources.yml')
        secrets = loadConfig('./data/secrets.yml')
        calendarConfigs = loadConfig('./calendars.yml')

        # Iterate through calendars in config
        for calendarConfigKey in calendarConfigs.keys():
            calendarConfig = calendarConfigs.get(calendarConfigKey)

            googleCalendar = factory.googleCalendar(calendarConfig, secrets)
            events = EventList()
            sourceKeys = calendarConfig.get('sources', [])

            # Iterate through sources in calendar config
            for sourceConfigKey in sourceKeys:
                events = events.merge(getEvents(sourceConfigKey, sourceConfigs))

            for event in events:
                event.deduplicate(forceUpdateIfMatched = options.force_update)
                if (not options.dry_run):
                    googleCalendar.syncEvent(event)
                    event.write()
                else:
                    googleCalendar.dryRun(event)

    except Exception as e:
        logger.exception("Exception occurred")

def parseArguments():
    parser = argparse.ArgumentParser(description='Scrape event pages and add them to a Google calendar')
    addLoggerArgsToParser(parser)
    parser.add_argument('-l', '--local', help = 'Whether to use local cached sources instead of re-scraping html.', action = 'store_false', default = True, dest = 'remote')
    parser.add_argument('-u', '--force-update', help = 'Whether to force Google Calendar updates, even if there\'s nothing to update.', action = 'store_true', default = False)
    parser.add_argument('-d', '--dry-run', help = 'Run the parser but do not write to the calendar or database.', action = 'store_true', default = False)

    return parser.parse_args()

def loadConfig(filename):
    with open(filename, 'r') as file:
        config = yaml.safe_load(file)
        return config

def getEvents(sourceConfigKey, sourceConfigs):

    sourceConfig = sourceConfigs.get(sourceConfigKey)
    source = factory.source(sourceConfigKey, sourceConfig)
    html = source.getHtml()

    parser = factory.parser(sourceConfigKey, sourceConfig)
    events = parser.parse(html).events

    logger.warning(len(events.events))
    events = factory.postTasks(events, sourceConfig)
    logger.warning(len(events.events))

    return events

if __name__ == '__main__':
    main()
