import re
from CalendarParser import CalendarParser
from Event import Event
from CalendarLogger import logger

class Space2640Parser(CalendarParser):

    def parseEvents(self, settings = {}):
        for eventHtml in self.soup().find_all('article', class_ = 'eventlist-event--upcoming'):
            logger.info('found')
            link = eventHtml.find('a').get('href')
            locationHtml = eventHtml.find('li', class_ = 'eventlist-meta-address')
            location = self.removeTagFromElement(locationHtml, 'a').get_text()
            location = self.replaceWhitespace(location, '')
            description = eventHtml.find('div', class_ = 'eventlist-description').get_text()
            title = eventHtml.find('h1', class_ = 'eventlist-title').get_text()
            date = eventHtml.find('time', class_ = 'event-date').get_text()
            startTime = eventHtml.find('time', class_ = 'event-time-12hr-start').get_text()
            endTime = eventHtml.find('time', class_ = 'event-time-12hr-end').get_text()

            event = Event()
            event.setSummary(title)
            event.setDescription(description)
            event.setLink(link)
            event.setLocation(location)
            event.setStartString(date + startTime, '%A, %B %d, %Y%I:%M %p')
            event.setEndString(date + endTime, '%A, %B %d, %Y%I:%M %p')

            self.addEvent(event)


            # primaryButtonHhtml = eventHtml.find_all('a', class_ = 'btn-primary')
            # if (primaryButtonHhtml):
            #     event = Event()
            #
            #     event.setDescription(self.replaceWhitespaceWithPipes(eventHtml.get_text()))
            #
            #     title = eventHtml.find('h2')
            #     event.setSummary(title.get_text())
            #
            #     locationHtml = eventHtml.find('a', class_ = 'venueLink')
            #     event.setLocation(locationHtml.get_text())
            #
            #     dateHtml = eventHtml.find('div', class_ = 'singleEventDate')
            #     date = dateHtml.get_text()
            #     timeHtml = eventHtml.find('div', class_ = 'eventDoorStartDate')
            #     time = re.findall('(\d+)(:\d\d)?(am|pm)', timeHtml.get_text())[0]
            #     event.setStartString(self.buildStartstamp(date, time), '\n%a, %b %d, %Y %I:%M%p')
            #     event.setAbsoluteEndDateTime(23, 59)
            #
            #     link = eventHtml.find('a')
            #     event.setLink(link.get('href'))
            #
            #     self.addEvent(event)

        return self

    def buildStartstamp(self, date, timePattern):
        return "%s %s%s%s" % (date, timePattern[0], timePattern[1] or ':00', timePattern[2])
