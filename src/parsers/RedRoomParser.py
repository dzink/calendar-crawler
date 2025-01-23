import re
from CalendarParser import CalendarParser
from Event import Event
from CalendarLogger import logger

class RedRoomParser(CalendarParser):

    def parseEvents(self, html, settings = {}):
        title = 'Unknown event'
        eventsHtml = self.soup(html).find('div', {'id': 'content-area'})
        for eventHtml in eventsHtml.find_all('div', class_ = 'home-post-area'):
            try:
                event = Event()

                titleHtml = eventHtml.find('h4')
                title = titleHtml.get_text()
                title = self.removeWhitespace(title)
                event.setSummary(title)

                dateHtml = eventHtml.find('h3')
                date = dateHtml.get_text()
                dateParsed = re.findall("(.*?)\s*\|\s*(.*?)\s*\|.*", date)
                day = dateParsed[0][0]
                time = dateParsed[0][1]
                if time == '':
                  time = '8:00 pm'
                date = '%s %s' % (day, time)
                event.setStartString(date, '%A %B %d, %Y %I:%M %p')


                linkHtml = eventHtml.find('a')
                if (linkHtml):
                    link = linkHtml.get('href')
                    event.setLink(link)

                descriptionHtml = eventHtml.find('p')
                description = descriptionHtml.get_text()
                description = self.cutPatternFromString(description, '>> MORE')
                description = self.removeWhitespace(description)
                description = '%s\n\n%s\n\n%s' % (title, date, description)
                event.setDescription(description)

                self.addEvent(event)

            except Exception as e:
                eventText = self.replaceWhitespaceWithPipes(eventHtml.get_text())
                logger.exception("Exception occurred in " + eventText)

        return self
