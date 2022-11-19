#!/usr/bin/python

import sys
sys.path.append('./src')
sys.path.append('./src/parsers')

import yaml
import argparse
from EventList import EventList
from CalendarFactory import CalendarFactory

from datetime import datetime
from dateutil.relativedelta import relativedelta

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

        sourceConfigs = loadConfig('./data/sources.yml')
        secrets = loadConfig('./data/secrets.yml')
        calendarConfigs = loadConfig('./data/calendars.yml')

        deadline = False

        if (not options.clean_all):
            deadline = datetime.now() - relativedelta(days=int(31))
            deadline = deadline.strftime('%Y-%m-%d')
        logger.info(deadline)

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
                # logger.info(sourceConfig)
                deadEvents = getExpiredEvents(deadline, sourceConfig['name'])
                events = events.merge(deadEvents)


            for event in events:
                if (options.dry_run):
                    if (event.calendarId):
                        googleCalendar.dryDeleteEvent(event)
                else:
                    if (event.calendarId):
                        googleCalendar.deleteEvent(event)
                    event.delete()

    except Exception as e:
        logger.exception("Exception occurred")


def parseArguments():
    parser = argparse.ArgumentParser(description='Clean old events from the calendar')
    addLoggerArgsToParser(parser)
    parser.add_argument('-d', '--dry-run', help = 'Run the cleaner but do not write to the calendar or database.', action = 'store_true', default = False)
    parser.add_argument('--clean-all', help = 'Clean all events', action = 'store_true', default = False)
    parser.add_argument('-s', '--source', help = 'Only crawl the given source(s).', action = 'append', default = None)


    return parser.parse_args()

def loadConfig(filename):
    with open(filename, 'r') as file:
        config = yaml.safe_load(file)
        return config

def getExpiredEvents(deadline, sourceConfigName = None):
    parameters = {}
    if (deadline):
        parameters['before'] = deadline
    if (sourceConfigName):
        parameters['sourceTitle'] = sourceConfigName
    deadEvents = EventList().find(parameters)
    logger.info('Found %d expired events for %s' % (len(deadEvents.events), sourceConfigName))
    return deadEvents

if __name__ == '__main__':
    main()
