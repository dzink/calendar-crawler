"""
CalendarParser

A parser reads the HTML of a page and converts it into events.

This class should be extended by parsers in src/parsers
"""

from bs4 import BeautifulSoup
import copy
import re
from EventList import EventList
from CalendarLogger import logger

class CalendarParser:

    def __init__(self, sourceTitle):
        self.events = EventList([])
        self.sourceTitle = sourceTitle

    def parse(self, html, settings=None):
        logger.debug('parsing beginning for ' + self.sourceTitle)
        self.parseEvents(html, settings or {})
        logger.debug('parsing completed for ' + self.sourceTitle)
        logger.info('%d events found in %s' % (len(self.events.events), self.sourceTitle))

        return self

    def makeSoup(self, html):
        return BeautifulSoup(html, features="html.parser")

    def parseEvents(self, html, settings=None):

        return self

    def addEvent(self, event):
        if (not event.sourceTitle):
            event.setSourceTitle(self.sourceTitle)
        self.events.add(event)

    def getEventsList(self):
        return (self.events)

    """
    Removes all occurances of a tag inside a bs4 object.
    """
    def removeTagFromElement(self, element, tag):
        scripts = element.find_all(tag)
        for script in scripts:
            script.extract()
        return element

    def replaceWhitespace(self, text, replace = ' | '):
        if (text is None):
            return text
        text = re.sub('(^\\s+)|(\\s+$)', '', text)
        text = re.sub('((\\s){2,})|\n', replace, text)
        return text

    def replaceWhitespaceWithPipes(self, text):
        return self.replaceWhitespace(text, ' | ')

    def getDescriptionText(self, element):
        if element is None:
            return ''
        el = copy.copy(element)
        for p in el.find_all('p'):
            p.insert_before('\n\n')
        for br in el.find_all('br'):
            br.insert_before('\n')
            br.decompose()
        text = el.get_text()
        text = re.sub(r'[^\S\n]*\n[^\S\n]*', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[^\S\n]{2,}', ' ', text)
        return text.strip()

    def parseStartAndEndTimesFromFuzzyString(self, string):
        """Parse start and end times from fuzzy strings like '7-9pm', 'doors at 8', 'noon'.
        Returns [startTime, endTime] where each is a string like '7:00pm' or None."""
        startTime = None
        endTime = None

        # This captures most of the variants.
        timeMatch = re.findall('((noon|((\\d+?):?(\\d\\d)?))\\s*((am|pm)?\\s*(-|to)\\s*(\\d+?):?(\\d\\d)?)?\\s*(am|pm))', string, re.IGNORECASE)

        # If this doesn't match, try a "Doors at ..." search.
        # There are a LOT of trivial parentheses in here, so that the positions match up with the above format
        if (not timeMatch):
            timeMatch = re.findall('doors (at|@) (noon|((\\d?)(:\\d\\d)?))\\s*(((((fff)))))?(am|pm)?', string, re.IGNORECASE)

        if (timeMatch):
            timeMatch = timeMatch[0]

            # Test for noon
            if ((timeMatch[1] == 'noon') or (timeMatch[1] == 'Noon')):
                startTime = "12:00pm"
            else:
                startTime = "%s:%s%s" % (timeMatch[3], timeMatch[4] or '00', timeMatch[6] or timeMatch[10] or 'pm')

            # Get end time if there is one.
            if (timeMatch[8]):
                endTime = "%s:%s%s" % (timeMatch[8], timeMatch[9] or '00', timeMatch[10] or 'pm')


        return [startTime, endTime]

    def removeOrdinalsFromNumbersInString(self, text):
        matches = re.findall('(.*)(\\dst|\\dnd|\\drd|\\dth)(.*)', text)
        if matches:
            text = '%s%s%s' % (matches[0][0], matches[0][1][0], matches[0][2])
        return text
