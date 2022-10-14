"""
CalendarParser

A parser reads the HTML of a page and converts it into events.

This class should be
"""

from bs4 import BeautifulSoup
import re
import pytz
from datetime import datetime
from EventList import EventList
from CalendarLogger import logger

class CalendarParser:

    def __init__(self, html, sourceTitle):
        self.events = []
        self.html = html
        self.sourceTitle = sourceTitle

    def parse(self, settings = {}):
        logger.info('parsing beginning for ' + self.sourceTitle)
        self.parseEvents(settings)
        logger.info('parsing completed for ' + self.sourceTitle)
        return self

    def soup(self):
        self.soup = BeautifulSoup(self.html, features="html.parser")
        return self.soup

    def parseEvents(self, settings = {}):

        return self

    def addEvent(self, event):
        if (not event.sourceTitle):
            event.setSourceTitle(self.sourceTitle)
        self.events.append(event)

    def getEventsList(self):
        return EventList(self.events)

    def removeTagFromElement(self, element, tag):
        scripts = element.find_all(tag)
        for script in scripts:
            script.extract()
        return element

    def removeScriptsFromElement(self, element):
        return self.removeTagFromElement(element, 'script')
        
    def replaceWhitespaceWithPipes(self, text):
        return self.replaceWhitespace(text, ' | ')

    def replaceWhitespace(self, text, replace = ' | '):
        text = re.sub('(^\s+)|(\s+$)', '', text)
        text = re.sub('((\s){2,})|\n', replace, text)
        return text

    """
    Convert inconsistent time indications to a common format
    A few common fuzzy time strings that this can capture:
        1-3pm
        noon
        9 am to 2 pm
        530-630
        doors at 7
    @returns Array with the startTime and endTime, if any
    """
    def parseStartAndEndTimesFromFuzzyString(self, string):
        startTime = None
        endTime = None

        # This captures most of the variants.
        timeMatch = re.findall('((noon|((\d+?):?(\d\d)?))\s*((am|pm)?\s*(-|to)\s*(\d+?):?(\d\d)?)?\s*(am|pm))', string, re.IGNORECASE)

        # If this doesn't match, try a "Doors at ..." search.
        # There are a LOT of trivial parentheses in here, so that the positions match up with the above format
        if (not timeMatch):
            timeMatch = re.findall('doors (at|@) (((\d?)(:\d\d)?))\s*(((((fff)))))?(am|pm)?', string, re.IGNORECASE)

        if (timeMatch):
            timeMatch = timeMatch[0]

            # Test for noon
            if (timeMatch[1] == 'noon'):
                startTime = "12:00pm"
            else:
                startTime = "%s:%s%s" % (timeMatch[3], timeMatch[4] or '00', timeMatch[6] or timeMatch[10] or 'pm')

            # Get end time if there is one.
            if (timeMatch[8]):
                endTime = "%s:%s%s" % (timeMatch[8], timeMatch[9] or '00', timeMatch[10] or 'pm')


        return [startTime, endTime]
