#!/usr/bin/python

import sys
sys.path.append('./src')

import argparse
from datetime import datetime
from EventList import EventList
from CalendarLogger import logger, addLoggerArgsToParser, buildLogger

options = None

 # date, pattern = '%Y-%m-%dT%H:%M:%S%z'):
 #    return date.strftime(pattern)

def main():
    try:
        parseArguments()
        buildLogger(options)

        print(options)
        parameters = {}
        today = datetime.now()

        if (options.summary):
            parameters['summary'] = options.summary
        if (options.source):
            parameters['sourceTitle'] = options.source
        if (options.description):
            parameters['description'] = options.description
        if (options.location):
            parameters['location'] = options.location
        if (options.date):
            parameters['date'] = options.date
        if (options.today):
            parameters['date'] = today.strftime('%Y-%m-%d')
        if (options.upcoming):
            parameters['upcoming'] = today.strftime('%Y-%m-%d')

        events = EventList().find(parameters)

        if (options.count):
            print('Events found: ' + str(len(events.events)))
        else:
            for event in events.events:
                print('-----------')
                print(event)

    except Exception as e:
        logger.exception("Exception occurred")

def parseArguments():
    global options
    parser = argparse.ArgumentParser(description='Scrape event pages and add them to a Google calendar')
    addLoggerArgsToParser(parser)
    parser.add_argument('-l', '--location', help = 'Search by location/venue', default = False)
    parser.add_argument('-s', '--summary', help = 'Search by title/artist/etc', default = False)
    parser.add_argument('-o', '--source', help = 'Search by import source', default = False)
    parser.add_argument('-d', '--date', help = 'Search by date in the format YYYY-MM-DD', default = False)
    parser.add_argument('-a', '--after', help = 'Search after a date in the format YYYY-MM-DD', default = False)
    parser.add_argument('-t', '--today', action = 'store_true', help = 'Search for events today', default = False)
    parser.add_argument('-u', '--upcoming', action = 'store_true', help = 'Search for upcoming events', default = False)
    parser.add_argument('-p', '--past', action = 'store_true', help = 'Search for past events', default = False)
    parser.add_argument('-e', '--description', help = 'Search by event descriptions', default = False)
    parser.add_argument('-c', '--count', action = 'store_true', help = 'Return the count only', default = False)

    options = parser.parse_args()

if __name__ == '__main__':
    main()
