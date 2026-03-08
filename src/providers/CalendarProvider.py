"""
CalendarProvider

Base class for external calendar sync targets (Google Calendar, CalDAV, etc.).
Subclasses must implement addEvent, updateEvent, and deleteEvent.
"""

from abc import ABC, abstractmethod
from CalendarItemsDb import CalendarItemsDb
from EventDb import EventDb
from Event import Event
from CalendarLogger import logger


class CalendarProvider(ABC):

    def __init__(self, providerId, config=None):
        self.providerId = providerId
        self.config = config or {}
        self.itemsDb = CalendarItemsDb()

    @abstractmethod
    def addEvent(self, event):
        """Add an event to the external calendar. Returns the external ID."""
        pass

    @abstractmethod
    def updateEvent(self, event, externalId):
        """Update an existing event on the external calendar."""
        pass

    @abstractmethod
    def deleteEvent(self, externalId):
        """Delete an event from the external calendar."""
        pass

    def getPendingEvents(self):
        """Return (event, syncRecord) pairs for all pending items in this provider."""
        pending = self.itemsDb.getPending(self.providerId)
        results = []
        for record in pending:
            eventData = EventDb().table.search(
                __import__('tinydb').where('id') == record['eventId']
            )
            if eventData:
                event = Event().fromJson(eventData[0])
                results.append((event, record))
            else:
                logger.warning('Pending sync record for missing event %s' % record['eventId'])
        return results

    def getPendingDeletes(self):
        """Return all sync records flagged for deletion."""
        return self.itemsDb.getPendingDeletes(self.providerId)

    def markSynced(self, eventId, externalId):
        """Mark an event as synced with the external service's ID."""
        self.itemsDb.markSynced(eventId, self.providerId, externalId)

    def deleteItem(self, eventId):
        """Remove a sync record for this provider."""
        self.itemsDb.delete(eventId, self.providerId)

    @staticmethod
    def filterAfter(pending, date):
        """Filter pending events to those starting on or after a date (YYYY-MM-DD)."""
        return [(e, r) for e, r in pending if e.startToString()[:10] >= date]

    @staticmethod
    def limit(pending, n):
        """Limit pending events to the first n."""
        return pending[:n]

    def syncPending(self, pending=None, dryRun=False):
        """Sync pending events and process deletions. Returns count of synced events.
        If pending is None, fetches all pending events from the DB."""
        synced = 0
        if pending is None:
            pending = self.getPendingEvents()

        for event, record in pending:
            externalId = record.get('externalId')
            if dryRun:
                if externalId:
                    logger.info('Dry run - Updating event \"%s\" from source \"%s\"' % (event.summary, event.sourceTitle))
                else:
                    logger.info('Dry run - Inserting event \"%s\" from source \"%s\"' % (event.summary, event.sourceTitle))
                synced += 1
                continue
            try:
                if externalId:
                    self.updateEvent(event, externalId)
                else:
                    externalId = self.addEvent(event)
                self.markSynced(event.id, externalId)
                synced += 1
            except Exception as e:
                logger.exception("Exception occurred")

        for record in self.getPendingDeletes():
            externalId = record.get('externalId')
            eventId = record['eventId']
            if dryRun:
                logger.info('Dry run - Deleting event %s' % eventId)
                continue
            if externalId:
                try:
                    self.deleteEvent(externalId)
                except Exception as e:
                    logger.exception("Exception occurred")
                    continue
            self.deleteItem(eventId)

        return synced
