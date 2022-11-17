"""
EventDb uses a tinydb database to store events that have been scraped.

This is useful for:
    - Querying shows via findy.py
    - Determining if an event is a duplicate or not
    - Updating events using an existing calendarId
"""

from tinydb import TinyDB, where, Query
from CalendarLogger import logger
import re

class EventDb:
    db = None
    table = None
    path = 'data/events-db.json'

    def __init__(self):
        if (EventDb.db == None):
            db = TinyDB(self.path)
            EventDb.db = db
            EventDb.table = db.table('events')

    def upsert(self, event):
        data = event.toJson()
        table = EventDb.table
        table.upsert(data, where('id') == data['id'])

    def update(self, event):
        data = event.toJson()
        table = EventDb.table
        table.update(data, where('id') == data['id'])

    """
    Anticipate that events may change on websites.
    Check a few scenarios where we would want to update the event instead of
    creating a new one.
    Returns the first match, or None if none.
    """
    def findDuplicate(self, data):
        table = EventDb.table

        #Match link
        results = table.search((where('link') == data['link']) & (where('link') != None) & (where('id') != data['id']))
        if (results):
            logger.debug('matched via link')
            return results[0]

        # Match location and datetime
        results = table.search((where('location') == data['location']) & (where('start') == data['start']) & (where('id') != data['id']))
        if (results):
            logger.debug('matched via location and datetime')
            return results[0]

        # Match event and day
        datePatten = '^' + data['start'][0:10]
        results = table.search((where('summary') == data['summary']) & (where('start').matches(datePatten)) & (where('id') != data['id']))
        if (results):
            logger.debug('matched via event and day')
            return results[0]

        return None

    """
    @TODO rotate out old events to keep the tinydb tiny.
    """
    def rotateOut(self):
        pass
    def find(self, parameters):


        query = (where('id') != None)
        q = Query()
        if 'summary' in parameters:
            query = query & self.queryMatches('summary', parameters['summary'])
        if 'sourceTitle' in parameters:
            query = query & self.queryMatches('sourceTitle', parameters['sourceTitle'])
        if 'description' in parameters:
            query = query & self.queryMatches('description', parameters['description'])
        if 'location' in parameters:
            query = query & self.queryMatches('location', parameters['location'])

        if 'date' in parameters:
            query = query & where('start').matches(parameters['date'])
        # if 'after' in parameters:
        #     query = query & (where('start') >= self.expandSearchDateString(parameters['upcoming']))
        if 'before' in parameters:
            query = query & (where('start') < self.expandSearchDateString(parameters['before']))
        if 'after' in parameters:
            query = query & where('start') >= self.expandSearchDateString(parameters['after'])

        results = EventDb.table.search(query)
        return results

    def queryMatches(self, parameter, match):
        return where(parameter).matches('.*' + match, flags=re.IGNORECASE)

    """
    For incomplete date strings, add some default days/times/etc
    """
    def expandSearchDateString(self, date):
        dateLen = len(date)
        if (dateLen < 18):
            defaultDate = '2022-01-01T00:00:00'
            date = date + defaultDate[(dateLen):]
        return date
