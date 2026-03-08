"""A collection of Event objects with merge, find, and iteration support."""

from Event import Event
from EventDb import EventDb


class EventList:

    def __init__(self, events=None):
        self.events = events or []

    def add(self, event):
        self.events.append(event)
        return self

    def merge(self, other):
        self.events = self.events + other.events
        return self

    def find(self, parameters={}):
        db = EventDb()
        results = db.find(parameters)
        if results:
            for result in results:
                event = Event().fromJson(result)
                self.add(event)
        return self

    def __iter__(self):
        return self.events.__iter__()
