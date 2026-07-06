#!python3./.venv/bin/python3

"""
One-time migration: copies calendarId from events-db into the calendar-items sync queue.
Each future event with a calendarId gets a record linking it to the given provider,
with status=0 (pending) and the Google Calendar event ID as externalId.

Usage: python migrate-calendar-items.py <providerId>
Example: python migrate-calendar-items.py dzShowCrawler
"""

import sys
sys.path.append('./src')
import paths

import argparse
from tinydb import TinyDB, where
from CalendarItemsDb import CalendarItemsDb

def main():
    parser = argparse.ArgumentParser(description='Migrate event calendarIds to the calendar-items sync queue.')
    parser.add_argument('providerId', help='The provider key to associate records with (e.g. dzShowCrawler)')
    args = parser.parse_args()

    eventsDb = TinyDB('data/events-db.json')
    eventsTable = eventsDb.table('events')
    itemsDb = CalendarItemsDb()

    events = eventsTable.search(where('calendarId') != None)
    migrated = 0
    skipped = 0

    for event in events:
        eventId = event['id']
        externalId = event['calendarId']
        existing = itemsDb.getByEventId(eventId, args.providerId)
        if existing:
            skipped += 1
            continue

        CalendarItemsDb.table.insert({
            'eventId': eventId,
            'providerId': args.providerId,
            'status': 0,
            'externalId': externalId,
        })
        migrated += 1

    print('%d events migrated, %d skipped (already exist).' % (migrated, skipped))

if __name__ == '__main__':
    main()
