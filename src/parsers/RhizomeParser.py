from CalendarParser import CalendarParser
from Event import Event
from CalendarLogger import logger

class RhizomeParser(CalendarParser):

    def parseEvents(self, html, settings = {}):
        title = 'Unknown event'
        eventsHtml = self.soup(html).find('div', class_ = 'summary-block-collection-type-events')
        for eventHtml in eventsHtml.find_all('div', class_ = 'summary-item-record-type-event'):
            try:
                title = eventHtml.find('div', class_ = 'summary-title').get_text()
                title = self.replaceWhitespace(title, ' ')
                event = Event()
                descriptionHtml = eventHtml.find('div', class_ = 'summary-excerpt')
                description = self.replaceWhitespaceWithPipes(descriptionHtml.get_text())
                # print(description)
                link = eventHtml.find('a').get('href')

                date = eventHtml.find('div', class_ = 'summary-thumbnail-event-date').get_text()
                date = self.replaceWhitespace(date, ' ')
                year = event.getNearestYear(date, '%b %d')

                # The time is always in the first paragraph
                topLine = descriptionHtml.find('p').get_text()
                startTime, endTime = self.parseStartAndEndTimesFromFuzzyString(topLine)

                if (startTime):
                    startStamp = '%s %s %s' % (year, date, startTime)
                else:
                    startStamp = '%s %s %s' % (year, date, '7:00pm')

                if (endTime):
                    endStamp = '%s %s %s' % (year, date, endTime)
                else:
                    endStamp = None

                event.setSummary(title)
                event.setDescription(description)
                event.setLink(link)
                event.setLocation("Rhizome - 6950 Maple St. NW, Washington DC")
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
