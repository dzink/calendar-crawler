import re
import pytz
from datetime import datetime
from EventDb import EventDb
import random
from copy import copy
from CalendarLogger import logger

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
        self.sourceTitle = None
        self.skipSync = None
        self.color = 'default'
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

    def setSourceTitle(self, sourceTitle):
        self.sourceTitle = sourceTitle
        return self

    def setCalendarId(self, calendarId):
        self.calendarId = calendarId
        return self

    def setColor(self, color):
        self.color = color
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

    """
    A few methods for printing out timestamps.
    """
    def startToString(self, pattern = '%Y-%m-%dT%H:%M:%S%z'):
        return self.dateToString(self.startDate, pattern)

    def endToString(self, pattern = '%Y-%m-%dT%H:%M:%S%z'):
        return self.dateToString(self.endDate, pattern)

    def dateToString(self, date, pattern = '%Y-%m-%dT%H:%M:%S%z'):
        return date.strftime(pattern)

    def setStartString(self, date, pattern = '%Y-%m-%dT%H:%M:%S%z'):
        self.startDate = self.parseDateString(date, pattern)
        return self

    """
    A few methods for converting strings into timestamps.
    """
    def setEndString(self, date, pattern = '%Y-%m-%dT%H:%M:%S%z'):
        self.endDate = self.parseDateString(date, pattern)
        return self

    def parseDateString(self, date, pattern = '%Y-%m-%dT%H:%M:%S%z'):
        dt = datetime.strptime(date, pattern)
        return self.localizeDate(dt)

    def localizeDate(self, date):
        if (date.tzinfo == None):
            tz = pytz.timezone(self.timeZone)
            date = tz.localize(date)
        return date

    """
    Some sources don't indicate the year. This will find the nearest possible
    year for a given date.
    """
    def getNearestYear(self, date, pattern = '%A %B %d'):
        dateCandidates = []
        pattern = pattern + ' %Y'
        now = self.localizeDate(datetime.now())
        years = [now.year - 1, now.year, now.year + 1]
        shortestYear = None
        shortestDifference = None
        for year in years:
            testDate = self.parseDateString(' '.join([date, str(year)]), pattern)
            difference = abs((now - testDate).total_seconds())
            if (shortestDifference == None or (difference < shortestDifference)):
                shortestYear = year
                shortestDifference = difference

        return shortestYear

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
            'color': self.color,
            'link': self.link,
            'sourceTitle': self.sourceTitle,
            'start': self.startToString(),
            'end': self.endToString(),
        }
        return data

    """
    Set event values from a JSON object. Any empty values will not be
    overwritten.
    """
    def fromJson(self, data):
        self.setId(data.get('id') or self.id)
        self.setSummary(data.get('summary') or self.summary)
        self.setSourceTitle(data.get('sourceTitle') or self.sourceTitle)
        self.setLocation(data.get('location') or self.location)
        self.setDescription(data.get('description') or self.description)
        self.setLink(data.get('link') or self.link)
        self.setCalendarId(data.get('calendarId') or self.calendarId)
        self.setColor(data.get('color') or self.color)
        self.setStartString(data.get('start') or self.startToString())
        self.setEndString(data.get('end') or self.endToString())
        return self

    """
    Determines whether this event matches a pattern. The criteria is an object
    where any property is a property on the event to search. The pattern should
    be a regex pattern.

    Sample criteria:
    {
        "location": "\\s*Horrible venue\\s*",
        "summary": "\\s*Bad Band I don't want to see\\s*",
    }

    @param data is a hash, in case we don't need to regenerate the data.
    """
    def matches(self, criteria, data = None, regex = True):
        if (not data):
            data = self.toJson()
        for property, pattern in criteria.items():
            if (regex and isinstance(pattern, str)):
                matches = re.search(pattern, data[property], re.IGNORECASE)
                if (matches == None):
                    return False
            else:
                if (pattern != data[property]):
                    logger.debug('%s not a match: "%s" :: "%s"' % (property, pattern, data[property]))
                    return False
        return True

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
    def deduplicate(self, forceUpdateIfMatched = False):
        data = self.toJson()
        logger.debug('searching for duplicate: ' + str(data))
        dupe = EventDb().findDuplicate(data)
        if (dupe):
            logger.debug('found duplicate: ' + str(dupe))
            self.updateFromDuplicate(dupe)
            data['id'] = dupe['id']
            data['calendarId'] = dupe['calendarId']
            if (not self.needsToUpdate(data, dupe)):
                if (not forceUpdateIfMatched):
                    self.skipSync = True
        return self

    """
    Takes data and a potential duplicate, and determines whether they need to
    be updated.
    """
    def needsToUpdate(self, data, dupe):
        return (not self.matches(dupe, data = data, regex = False))

    """
    Merge the properties that one would want to keep from a dupe.
    """
    def updateFromDuplicate(self, data):
        self.setId(data['id'] or self.id)
        self.setCalendarId(data['calendarId'] or self.calendarId)

    """
    Sets an absolute end time on the same day as the start time.
    """
    def setAbsoluteEndDateTime(self, hour = 23, minute = 59):
        dt = copy(self.startDate)
        dt = dt.replace(hour = hour, minute = minute)
        self.setEnd(dt)

    def prefixDescriptionWithLink(self):
        self.description = '\n\n'.join([self.link, self.description])

    def __str__(self):
        string = "ID: %s\n\tSummary: %s\n\tStart: %s\n\tEnd: %s\n\tLocation: %s\n\tDescription: %s\n\tLink: %s\n\tSource: %s\n\tcalendarId: %s\n\tcolor: %s" %(self.id, self.summary, self.startToString(), self.endToString(), self.location, self.description, self.link, self.sourceTitle, self.calendarId, self.color)
        return string
