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
