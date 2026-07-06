#!python3./.venv/bin/python3

"""
Delete ALL events from the remote Google Calendar.

This does NOT delete the calendar itself, only its events.

Usage:
    python scripts/nuke-google-events.py          # dry run (default)
    python scripts/nuke-google-events.py --confirm # actually delete
"""

import sys
sys.path.append('./src')
import paths

from Config import Config
from Factory import CalendarFactory
from CalendarLogger import logger, addLoggerArgsToParser, buildLogger
import argparse


def main():
    cfg = Config()
    config = cfg.loadOptions()
    options = parseArguments(config)
    buildLogger(options)

    calendarConfigs = cfg.loadCalendars()
    secrets = cfg.loadSecrets()
    factory = CalendarFactory(options, config, secrets)

    for calendarKey in calendarConfigs:
        calendarConfig = calendarConfigs.get(calendarKey)
        providers = factory.providers(calendarKey, calendarConfig)

        for provider in providers:
            gcal = provider
            service = gcal.service()
            calendarId = gcal.googleCalendarId

            print('Listing events on calendar: %s' % calendarId)

            deleted = 0
            page_token = None
            while True:
                result = service.events().list(
                    calendarId=calendarId,
                    maxResults=250,
                    pageToken=page_token,
                    singleEvents=True,
                    orderBy='startTime',
                ).execute()

                items = result.get('items', [])
                if not items and not page_token:
                    print('No events found.')
                    break

                for item in items:
                    eid = item['id']
                    summary = item.get('summary', '(no title)')
                    created = item.get('created', '?')[:10]
                    if options.confirm:
                        try:
                            service.events().delete(calendarId=calendarId, eventId=eid).execute()
                            print('  Deleted: %s — %s — %s — %s' % (created, calendarId, eid, summary))
                            deleted += 1
                        except Exception as e:
                            print('  FAILED: %s — %s — %s — %s — %s' % (created, calendarId, eid, summary, e))
                    else:
                        print('  Would delete: %s — %s — %s — %s' % (created, calendarId, eid, summary))
                        deleted += 1

                page_token = result.get('nextPageToken')
                if not page_token:
                    break

            print('%d events %s from Google Calendar.' % (
                deleted, 'deleted' if options.confirm else 'would be deleted'))


def parseArguments(config):
    parser = argparse.ArgumentParser(description='Delete all events from Google Calendar')
    addLoggerArgsToParser(parser, config.get('logging', {}))
    parser.add_argument('--confirm', help='Actually delete. Without this flag, dry run only.', action='store_true', default=False)
    return parser.parse_args()


if __name__ == '__main__':
    main()
