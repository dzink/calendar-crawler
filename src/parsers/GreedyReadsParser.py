from CalendarParser import CalendarParser
from Event import Event
from CalendarLogger import logger

class GreedyReadsParser(CalendarParser):

    def parseEvents(self, html, settings = {}):
        title = 'Unknown event'
        eventsHtml = self.soup(html).find('div', {'id': 'maintable'})
        for eventHtml in eventsHtml.find_all('div', class_ = 'ant-row'):
            try:
                header = eventHtml.find('h2')
                title = header.get_text()
                event = Event()

                descriptionHtml = eventHtml.find('div', class_ = 'html')
                if descriptionHtml:
                    event.setDescription(descriptionHtml.get_text())
                    linkHtml = descriptionHtml.find('a', href=True)
                    if linkHtml:
                        event.setLink(linkHtml['href'])


                timeStampHtml = header.find('span')
                if timeStampHtml:
                    timeStamp = timeStampHtml.get_text()
                    title = self.cutPatternFromString(title, timeStamp)
                    date = self.cutPatternFromString(timeStamp, ' @.*')
                    date = self.removeOrdinalsFromNumbersInString(date)
                    startTime, endTime = self.parseStartAndEndTimesFromFuzzyString(timeStamp)
                    event.setSummary(title)
                    if (startTime):
                        startStamp = '%s %s' % (date, startTime)
                    else:
                        startStamp = '%s %s' % (date, '7:00pm')
                    event.setStartString(startStamp, '%A %B %d, %Y %I:%M%p')

                    if (endTime):
                        endStamp = '%s %s' % (date, endTime)
                        event.setEndString(endStamp, '%A %B %d, %Y %I:%M%p')

                    self.addEvent(event)

            except Exception as e:
                eventText = self.replaceWhitespaceWithPipes(eventHtml.get_text())
                logger.exception("Exception occurred in " + eventText)

        return self
