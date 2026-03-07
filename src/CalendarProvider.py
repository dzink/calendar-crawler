"""
CalendarProvider

Base class for external calendar sync targets (Google Calendar, CalDAV, etc.).
Provides methods to query pending sync items and mark them as synced.
Subclasses implement the actual API calls.
"""

from CalendarItemsDb import CalendarItemsDb
from EventDb import EventDb
from Event import Event
from CalendarLogger import logger


class CalendarProvider:

    def __init__(self, providerId, config=None):
        self.providerId = providerId
        self.config = config or {}
        self.itemsDb = CalendarItemsDb()

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

    def markSynced(self, eventId, externalId):
        """Mark an event as synced with the external service's ID."""
        self.itemsDb.markSynced(eventId, self.providerId, externalId)

    def deleteItem(self, eventId):
        """Remove a sync record for this provider."""
        self.itemsDb.delete(eventId, self.providerId)
