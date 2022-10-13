import pytz
from datetime import datetime
from Event import Event
from EventDb import EventDb
from CalendarLogger import logger

class EventList:

    def __init__(self, events = []):
        self.events = events


    def add(self, event):
        self.events.append(event)

    """
    Creates an endtime element on all events, where the date is the same, but
    the hour and minute are set to an absolute amount.
    """
    def setAbsoluteEndDateTime(self, hour = 23, minute = 59):
        for event in self.events:
            event.setAbsoluteEndDateTime(hour, minute)

    def addBoilerplateToDescriptions(self, boilerplate):
        for event in self.events:
            event.setDescription('\n\n'.join([event.description or '', boilerplate]))

    def prefixDescriptions(self, prefix):
        for event in self.events:
            event.setDescription(''.join([prefix, event.description or '']))

    def prefixLinks(self, prefix):
        for event in self.events:
            event.setLink(''.join([prefix, event.link or '']))

    def setLocationAddress(self, address):
        for event in self.events:
            event.setLocation(''.join([event.location or '', address]))

    def prefixDescriptionsWithLinks(self):
        for event in self.events:
            event.prefixDescriptionWithLink()

    def setColors(self, color):
        for event in self.events:
            event.setColor(color)

    def deduplicate(self):
        for event in self.events:
            event.deduplicate()

    def write(self):
        for event in self.events:
            event.write()

    """
    Filters to only leave any events that match a pattern. The criteria is an
    object where any property is a property on the event to search. The pattern
    should be a regex pattern.

    Sample criteria:
    {
        "location": "Cool venue",
        "summary": "Nice band",
    }
    """
    def selectEvents(self, criteria, regex = True, negate = False):
        selected = EventList()
        for event in self.events:
            match = event.matches(criteria, regex = regex)
            if ((not negate and match) or (negate and not match)):
                selected.add(event)
        return selected

    def rejectEvents(self, criteria, regex = True):
        return self.selectEvents(criteria, regex, negate = True)


    def find(self, parameters = {}):
        db = EventDb()
        results = db.find(parameters)
        if (results):
            for result in results:
                event = Event().fromJson(result)
                self.add(event)
        return self
