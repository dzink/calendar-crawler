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
                    time = ('8', ':00', 'pm')

                    description = self.replaceWhitespaceWithPipes(eventHtml.get_text())
                    event.setDescription(description)

                    title = eventHtml.find('h2')
                    title = self.replaceWhitespaceWithPipes(title.get_text())
                    event.setSummary(title)

                    locationHtml = eventHtml.find('a', class_ = 'venueLink')
                    if (locationHtml):
                        event.setLocation(locationHtml.get_text())

                    dateHtml = eventHtml.find('div', class_ = 'eventDateList')
                    date = dateHtml.get_text()

                    # Need to replace shortened months for parsing purposes.
                    date = self.replaceDictionary(date, {
                        'June': 'Jun',
                        'July': 'Jul',
                        'Sept': 'Sep',
                    })
                    date = self.replaceWhitespace(date, '')
                    date = self.stripMultipleDates(date)

                    timeHtml = eventHtml.find('div', class_ = 'eventDoorStartDate')
                    if (timeHtml):
                        time = re.findall('(\d+)(:\d\d)?(am|pm)', timeHtml.get_text())[0]

                    try:
                        event.setStartString(self.buildStartstamp(date, time), '%a, %b %d, %Y %I:%M%p')
                    except:

                        # Sometimes the date doesn't have a year
                        year = event.getNearestYear(date, '%a, %b %d')
                        date = date + ", " + str(year)
                        event.setStartString(self.buildStartstamp(date, time), '%a, %b %d, %Y %I:%M%p')

                    event.setAbsoluteEndDateTime(23, 59)

                    link = eventHtml.find('a').get('href')
                    event.setLink(link)
                    if (link):
                        self.addEvent(event)
            except Exception as e:
                eventText = self.replaceWhitespaceWithPipes(eventHtml.get_text())
                logger.exception("Exception occurred in " + eventText)

        return self

    def buildStartstamp(self, date, timePattern):
        return "%s %s%s%s" % (date, timePattern[0], timePattern[1] or ':00', timePattern[2])

    def stripMultipleDates(self, date):
        pattern = re.findall('^(.+?, .+? \d+)(\\s\\-\\s.*)?', date)
        return pattern[0][0]
