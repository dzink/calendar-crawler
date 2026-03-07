"""
CalendarItemsDb

A sync queue that tracks which events need to be pushed to external calendars.
Each record stores an eventId + providerId (unique together), a status,
and the externalId returned by the remote service after syncing.

status: 0 = pending sync, 1 = synced
"""

from tinydb import TinyDB, where
from CalendarLogger import logger


class CalendarItemsDb:
    db = None
    table = None
    path = 'data/calendar-items-db.json'

    def __init__(self):
        if CalendarItemsDb.db is None:
            db = TinyDB(self.path)
            CalendarItemsDb.db = db
            CalendarItemsDb.table = db.table('calendarItems')

    def upsert(self, eventId, providerId, status=0):
        """Insert or update a sync record. Marks it pending by default."""
        table = CalendarItemsDb.table
        record = {
            'eventId': eventId,
            'providerId': providerId,
            'status': status,
        }
        existing = table.search(
            (where('eventId') == eventId) & (where('providerId') == providerId)
        )
        if existing:
            table.update(
                {'status': status},
                (where('eventId') == eventId) & (where('providerId') == providerId)
            )
        else:
            record['externalId'] = None
            table.insert(record)

    def markSynced(self, eventId, providerId, externalId):
        """Mark a record as synced with the external calendar's ID."""
        table = CalendarItemsDb.table
        table.update(
            {'status': 1, 'externalId': externalId},
            (where('eventId') == eventId) & (where('providerId') == providerId)
        )

    def getPending(self, providerId):
        """Return all records with status=0 for a given provider."""
        table = CalendarItemsDb.table
        return table.search(
            (where('providerId') == providerId) & (where('status') == 0)
        )

    def delete(self, eventId, providerId):
        """Remove a sync record."""
        table = CalendarItemsDb.table
        table.remove(
            (where('eventId') == eventId) & (where('providerId') == providerId)
        )

    def upsertSyncStatus(self, events, providerId):
        """Mark events as unsynced (pending) if they are new to this provider."""
        table = CalendarItemsDb.table
        existing = table.search(where('providerId') == providerId)
        existingIds = {record['eventId'] for record in existing}
        for event in events:
            if event.skipSync:
                continue
            if event.id not in existingIds:
                self.upsert(event.id, providerId, status=0)

    def getByEventId(self, eventId, providerId):
        """Look up a single record."""
        table = CalendarItemsDb.table
        results = table.search(
            (where('eventId') == eventId) & (where('providerId') == providerId)
        )
        return results[0] if results else None
