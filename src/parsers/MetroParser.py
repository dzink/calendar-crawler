from CalendarParser import CalendarParser
from Event import Event
from CalendarLogger import logger

class MetroParser(CalendarParser):

    def parseEvents(self, html, settings = {}):
        # raise Exception()
        title = 'Unknown event'
        eventsHtml = self.soup(html).find('div', class_ = 'listings-block-listgrid')
        for eventHtml in eventsHtml.find_all('div', class_ = 'listings-block-list__listing'):
            try:
                title = eventHtml.find('h3', class_ = 'listing__title').get_text()
                title = self.replaceWhitespace(title, ' ')
                event = Event()
                tickets_link = eventHtml.find('a', class_ = 'JS--buyTicketsButton').get('href')
                more_link = eventHtml.find('a', class_ = 'plotButton--secondary').get('href')

                date = eventHtml.find('span', class_ = 'listing-date-time__date').get_text()
                date_members = self.parseDateFromFuzzyString(date)
                date_string = '%s %s' % (date_members[1], date_members[2])
                year = event.getNearestYear(date_string, '%b %d')

                startTime, endTime = self.parseStartAndEndTimesFromFuzzyString(date)

                if (startTime):
                    startStamp = '%s %s %s' % (year, date_string, startTime)
                else:
                    startStamp = '%s %s %s' % (year, date_string, '7:00pm')

                if (endTime):
                    endStamp = '%s %s %s' % (year, date_string, endTime)
                else:
                    endStamp = None

                event.setSummary(title)
                description = ' read more: %s , tickets: %s ' % (more_link, tickets_link)
                event.setDescription(description)
                event.setLocation('Metro Gallery')
                event.setLink(more_link)
                event.setStartString(startStamp, '%Y %b %d %I:%M%p')
                if (endStamp):
                    event.setEndString(endStamp, '%Y %b %d %I:%M%p')
                else:
                    event.setAbsoluteEndDateTime(22, 0)

                self.addEvent(event)

            except Exception as e:
                eventText = self.replaceWhitespaceWithPipes(eventHtml.get_text())
                logger.exception("Exception occurred in " + eventText)

        return self
