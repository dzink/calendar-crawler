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
        """Mark events as pending sync if they are new or updated."""
        for event in events:
            if event.skipSync:
                continue
            self.upsert(event.id, providerId, status=0)

    def markDeleted(self, eventId):
        """Flag all sync records for an event as pending deletion."""
        table = CalendarItemsDb.table
        table.update({'pendingDelete': True}, where('eventId') == eventId)

    def getPendingDeletes(self, providerId):
        """Return all records flagged for deletion for a given provider."""
        table = CalendarItemsDb.table
        return table.search(
            (where('providerId') == providerId) & (where('pendingDelete') == True)
        )

    def getByEventId(self, eventId, providerId):
        """Look up a single record."""
        table = CalendarItemsDb.table
        results = table.search(
            (where('eventId') == eventId) & (where('providerId') == providerId)
        )
        return results[0] if results else None
