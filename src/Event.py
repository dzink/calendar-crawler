import re
import pytz
from datetime import datetime
from EventDb import EventDb
import random
from copy import copy

class Event:

    timeZone = 'US/Eastern'

    def __init__(self):
        self.summary = None
        self.location = None
        self.description = None
        self.startDate = None
        self.endDate = None
        self.calendarId = None
        self.id = None
        self.link = None
        self.skipSync = None
        self.buildId()

    def buildId(self):
        self.id = random.getrandbits(128)

    def setId(self, id):
        self.id = id
        return self

    def setSummary(self, summary):
        self.summary = summary
        return self

    def setLocation(self, location):
        self.location = location
        return self

    def setDescription(self, description):
        self.description = description
        return self

    def setLink(self, link):
        self.link = link
        return self

    def setCalendarId(self, calendarId):
        self.calendarId = calendarId
        return self

    def setStart(self, startDate):
        self.startDate = startDate
        return self

    def setEnd(self, endDate):
        self.endDate = endDate
        return self

    def setStartDate(self, date):
        self.date = date
        return self

    def startToString(self, pattern = '%Y-%m-%dT%H:%M:%S%z'):
        return self.dateToString(self.startDate, pattern)

    def endToString(self, pattern = '%Y-%m-%dT%H:%M:%S%z'):
        return self.dateToString(self.endDate, pattern)

    def dateToString(self, date, pattern = '%Y-%m-%dT%H:%M:%S%z'):
        return date.strftime(pattern)

    def setStartString(self, date, pattern = '%Y-%m-%dT%H:%M:%S%z'):
        self.startDate = self.parseDateString(date, pattern)
        return self

    def setEndString(self, date, pattern = '%Y-%m-%dT%H:%M:%S%z'):
        self.endDate = self.parseDateString(date, pattern)
        return self

    def parseDateString(self, date, pattern = '%Y-%m-%dT%H:%M:%S%z'):
        dt = datetime.strptime(date, pattern)
        if (dt.tzinfo == None):
            tz = pytz.timezone(self.timeZone)
            dt = tz.localize(dt)
        return dt

    """
    Create a JSON object from this event.
    """
    def toJson(self):
        data = {
            'id': self.id,
            'summary': self.summary,
            'location': self.location,
            'description': self.description,
            'calendarId': self.calendarId,
            'link': self.link,
            'start': self.startToString(),
            'end': self.endToString(),
        }
        return data

    """
    Set event values from a JSON object. Any empty values will not be
    overwritten.
    """
    def fromJson(self, data):
        self.setId(data['id'] or self.id)
        self.setSummary(data['summary'] or self.summary)
        self.setLocation(data['location'] or self.location)
        self.setDescription(data['description'] or self.description)
        self.setLink(data['link'] or self.link)
        self.setCalendarId(data['calendarId'] or self.calendarId)
        self.setStartString(data['start'] or self.startToString())
        self.setEndString(data['end'] or self.endToString())

    """
    Determines whether this event matches a pattern. The criteria is an object
    where any property is a property on the event to search. The pattern should
    be a regex pattern.

    Sample criteria:
    {
        "location": "\\s*Horrible venue\\s*",
        "summary": "\\s*Bad Band I don't want to see\\s*",
    }
    """
    def match(self, criteria):
        event = self.__dict__
        for property, pattern in criteria.items():
            matches = re.search(pattern, event[property], re.IGNORECASE)
            if (matches != None):
                return True
        return False

    def write(self):
        EventDb().upsert(self)
        return self

    def writeUpdate(self):
        EventDb().update(self)
        return self

    """
    If there are any duplicates in the database, find them and take their
    id and calendarId.
    """
    def deduplicate(self):
        data = self.toJson()
        dupe = EventDb().findDuplicate(data)
        if (dupe):
            self.fromDuplicate(dupe)
            data['id'] = dupe['id']
            data['calendarId'] = dupe['calendarId']
            if (data == dupe):
                print('does not need to update')
                self.skipSync = True
            else:
                print('needs to update')
                print([data, dupe])
        return self

    def setAbsoluteEndDateTime(self, hour = 23, minute = 59):
        dt = copy(self.startDate)
        dt = dt.replace(hour = hour, minute = minute)
        self.setEnd(dt)

    """
    Merge the properties that one would want to keep from a dupe.
    """
    def fromDuplicate(self, data):
        self.setId(data['id'] or self.id)
        self.setCalendarId(data['calendarId'] or self.calendarId)

    def __str__(self):
        string = "ID: %s\nSummary: %s\nStart: %s\nEnd: %s\nLocation: %s\nDescription: %s\nLink: %s\ncalendarId: %s" %(self.id, self.summary, self.startToString(), self.endToString(), self.location, self.description, self.link, self.calendarId)
        return string
