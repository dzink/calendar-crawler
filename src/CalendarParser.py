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

class CalendarParser:

    def __init__(self, html, sourceTitle):
        self.events = []
        self.html = html
        self.sourceTitle = sourceTitle

    def parse(self, settings = {}):
        self.parseEvents(settings)
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

    def removeScriptsFromElement(self, element):
        scripts = element.find_all('script')
        for script in scripts:
            script.extract()
        return element

    def replaceWhitespaceWithPipes(self, text):
        text = re.sub('(^\s+)|(\s+$)', '', text)
        text = re.sub('((\s){2,})|\n', ' | ', text)
        return text
