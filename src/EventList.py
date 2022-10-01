import pytz
from datetime import datetime

class EventList:

    def __init__(self, events):
        self.events = events

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
            # event['location'] = ''.join([event['location'], address])

    def prefixDescriptionsWithLinks(self):
        for event in self.events:
            event.setDescription('\n\n'.join([event.link, event.description or '']))

    def deduplicate(self):
        for event in self.events:
            event.deduplicate()

    def write(self):
        for event in self.events:
            event.write()

    """
    Removes any events that match a pattern. The criteria is an object where any
    property is a property on the event to search. The pattern should be a
    regex pattern.

    Sample criteria:
    {
        "location": "\\s*Horrible venue\\s*",
        "summary": "\\s*Bad Band I don't want to see\\s*",
    }
    """
    def rejectEvents(self, criteria):
        filteredEvents = []
        for event in self.events:
            add = True
            for property, pattern in criteria.items():
                matches = re.search(pattern, event[property], re.IGNORECASE)
                if (matches != None):
                    add = False
            if (add):
                filteredEvents.append(event)
        self.events = filteredEvents
        return self
