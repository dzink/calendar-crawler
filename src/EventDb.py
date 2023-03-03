"""
EventDb uses a tinydb database to store events that have been scraped.

This is useful for:
    - Querying shows via findy.py
    - Determining if an event is a duplicate or not
    - Updating events using an existing calendarId
"""

import re
from tinydb import TinyDB, where
from CalendarLogger import logger

class EventDb:
    db = None
    table = None
    path = 'data/events-db.json'

    def __init__(self):
        if (EventDb.db is None):
            database = TinyDB(self.path)
            EventDb.db = database
            EventDb.table = database.table('events')

    def upsert(self, event):
        """ Either inserts or updates an event to the db.

        event - an Event.
        """
        data = event.toJson()
        table = EventDb.table
        table.upsert(data, where('id') == data['id'])

    def update(self, event):
        """ Updates an existing event to the db.

        event - an Event that must have an id that exists in the db.
        """
        data = event.toJson()
        table = EventDb.table
        table.update(data, where('id') == data['id'])

    def delete(self, event):
        """ Deletes an event from the db.

        event - an Event that must have an id that exists in the db.
        """
        data = event.toJson()
        table = EventDb.table
        table.remove(where('id') == data['id'])
        logger.info('deleted %s' % data)

    def findDuplicate(self, data):
        """
        Anticipate that events may change on websites.
        Check a few scenarios where we would want to update the event instead of
        creating a new one.
        Returns the first match, or None if none.
        """
        table = EventDb.table

        #Match link
        results = table.search((where('link') == data['link']) & (where('link') is not None) &
            (where('id') != data['id']))
        if (results):
            logger.debug('matched via link')
            return results[0]

        # Match location and datetime
        results = table.search((where('location') == data['location']) &
            (where('start') == data['start']) & (where('id') != data['id']))
        if (results):
            logger.debug('matched via location and datetime')
            return results[0]

        # Match event and day
        datePatten = '^' + data['start'][0:10]
        results = table.search((where('summary') == data['summary']) &
            (where('start').matches(datePatten)) & (where('id') != data['id']))
        if (results):
            logger.debug('matched via event and day')
            return results[0]

        return None

    def rotateOut(self):
        # pylint: disable=pointless-string-statement, unnecessary-pass
        """
        @TODO rotate out old events to keep the tinydb tiny.
        """
        pass


    def find(self, parameters):
        """ Finds events in the database based on a query.

        parameters -- a hash of keys and values.
        """

        query = (where('id') is not None)

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
        if 'before' in parameters:
            before = self.expandSearchDateString(parameters['before'])
            query = query & (where('start') < before)
        if 'after' in parameters:
            after = self.expandSearchDateString(parameters['after'])
            query = query & (where('start') > after)

        results = EventDb.table.search(query)
        return results

    def queryMatches(self, parameter, match):
        """ Creates a grep-link query condition that matches anywhere in a string. """
        return where(parameter).matches('.*' + match, flags=re.IGNORECASE)

    def expandSearchDateString(self, date):
        """ Adds days or times to incomplete date strings."""
        dateLen = len(date)
        if (dateLen < 18):
            defaultDate = '2022-01-01T00:00:00'
            date = date + defaultDate[(dateLen):]
        return date
