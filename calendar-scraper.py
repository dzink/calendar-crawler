#!/usr/bin/python

import sys
sys.path.append('./src')
sys.path.append('./src/parsers')

import yaml
import argparse
from EventList import EventList
from GoogleCalendarBuilder import GoogleCalendarBuilder
from CalendarFactory import CalendarFactory

from time import sleep
from CalendarLogger import logger, addLoggerArgsToParser, buildLogger

options = None

def main():
    try:
        global options
        sourcesConfig = loadConfig('./sources.yml')
        options = parseArguments()
        buildLogger(options)

        gcb = GoogleCalendarBuilder()
        calendarId = gcb.getCalendarIdFromFile('data/calendarid.txt')

        events = EventList()
        for sourceConfigKey in sourcesConfig.keys():
            events = events.merge(getEvents(sourceConfigKey, sourcesConfig))

        logger.warning(len(events.events))

        for event in events:
            event.deduplicate(forceUpdateIfMatched = options.force_update)
            if (not options.dry_run):
                gcb.syncEvent(event, calendarId)
                event.write()
            else:
                gcb.dryRun(event)

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

def getEvents(sourceConfigKey, sourcesConfig):
    factory = CalendarFactory(options)

    sourceConfig = sourcesConfig.get(sourceConfigKey)
    source = factory.source(sourceConfigKey, sourceConfig)
    html = source.getHtml()

    parser = factory.parser(sourceConfigKey, sourceConfig, html)
    events = parser.parse().events

    logger.warning(len(events.events))
    events = factory.postTasks(events, sourceConfig)
    logger.warning(len(events.events))

    return events

if __name__ == '__main__':
    main()
