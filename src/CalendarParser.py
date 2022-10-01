from bs4 import BeautifulSoup
import re
import pytz
from datetime import datetime
from EventList import EventList

class CalendarParser:

    def __init__(self, html):
        self.events = []
        self.html = html

    def parse(self, settings = []):
        self.parseEvents()
        return self

    def soup(self):
        self.soup = BeautifulSoup(self.html, features="html.parser")
        return self.soup

    def parseEvents(self, postOffset = 0):

        return self

    def addEvent(self, event):
        self.events.append(event)

    def removeScripts(self, element):
        scripts = element.find_all('script')
        for script in scripts:
            script.extract()
        return element

    def getEvents(self):
        return EventList(self.events)
