# from bs4 import BeautifulSoup
import re
# import pytz
# from datetime import datetime
from CalendarParser import CalendarParser
from Event import Event

class OttobarParser(CalendarParser):

    def parseEvents(self, settings = {}):
        for eventHtml in self.soup().find_all('div', class_ = 'eventWrapper'):
            primaryButtonHhtml = eventHtml.find_all('a', class_ = 'btn-primary')
            if (primaryButtonHhtml):
                event = Event()

                event.setDescription(self.replaceWhitespaceWithPipes(eventHtml.get_text()))

                title = eventHtml.find('h2')
                event.setSummary(title.get_text())

                locationHtml = eventHtml.find('a', class_ = 'venueLink')
                event.setLocation(locationHtml.get_text())

                dateHtml = eventHtml.find('div', class_ = 'singleEventDate')
                date = dateHtml.get_text()
                timeHtml = eventHtml.find('div', class_ = 'eventDoorStartDate')
                time = re.findall('(\d+)(:\d\d)?(am|pm)', timeHtml.get_text())[0]
                event.setStartString(self.buildStartstamp(date, time), '\n%a, %b %d, %Y %I:%M%p')
                event.setAbsoluteEndDateTime(23, 59)

                link = eventHtml.find('a')
                event.setLink(link.get('href'))

                self.addEvent(event)

        return self

    def buildStartstamp(self, date, timePattern):
        return "%s %s%s%s" % (date, timePattern[0], timePattern[1] or ':00', timePattern[2])