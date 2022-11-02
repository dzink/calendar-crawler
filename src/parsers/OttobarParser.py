import re
from CalendarParser import CalendarParser
from Event import Event
from CalendarLogger import logger


class OttobarParser(CalendarParser):

    def parseEvents(self, html, settings = {}):
        for eventHtml in self.soup(html).find_all('div', class_ = 'eventWrapper'):
            try:
                primaryButtonHhtml = eventHtml.find_all('a', class_ = 'btn-primary')
                if (primaryButtonHhtml):
                    event = Event()

                    description = self.replaceWhitespaceWithPipes(eventHtml.get_text())
                    event.setDescription(description)

                    title = eventHtml.find('h2')
                    title = self.replaceWhitespaceWithPipes(title.get_text())
                    event.setSummary(title)

                    locationHtml = eventHtml.find('a', class_ = 'venueLink')
                    event.setLocation(locationHtml.get_text())

                    dateHtml = eventHtml.find('div', class_ = 'singleEventDate')
                    date = dateHtml.get_text()
                    timeHtml = eventHtml.find('div', class_ = 'eventDoorStartDate')
                    time = re.findall('(\d+)(:\d\d)?(am|pm)', timeHtml.get_text())[0]

                    try:
                        event.setStartString(self.buildStartstamp(date, time), '\n%a, %b %d, %Y %I:%M%p')
                    except:

                        # Sometimes the date doesn't have a year
                        year = event.getNearestYear(date, '\n%a, %b %d')
                        date = date + ", " + str(year)
                        event.setStartString(self.buildStartstamp(date, time), '\n%a, %b %d, %Y %I:%M%p')

                    event.setAbsoluteEndDateTime(23, 59)

                    link = eventHtml.find('a').get('href')
                    event.setLink(link)
                    if (link):
                        self.addEvent(event)
            except Exception as e:
                logger.exception("Exception occurred")
        return self

    def buildStartstamp(self, date, timePattern):
        return "%s %s%s%s" % (date, timePattern[0], timePattern[1] or ':00', timePattern[2])
