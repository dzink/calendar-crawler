from CalendarParser import CalendarParser
from Event import Event
from CalendarLogger import logger
import re

class WithFriendsParser(CalendarParser):

    def parseEvents(self, html, settings = {}):
        for eventHtml in self.soup(html).find_all('li', class_='wf-event'):
            try:
                event = Event()

                link = eventHtml.find('a')
                link = ''.join(['https://withfriends.co', link.get('href')])
                event.setLink(link)

                title = eventHtml.find('h4')
                event.setSummary(title.get_text())

                dateTime = eventHtml.find(attrs={
                    'data-type': 'Date_Time',
                    'data-kind': 'Item',
                })
                date = dateTime.get_text()

                # Sometimes WithFriends includes a year, sometimes it doesn't.
                if (re.findall('\d\d\d\d', date)):
                    event.setStartString(date, '%A, %B %d, %Y at %I:%M %p')
                else:
                    date = date + str(event.getNearestYear(date, '%A, %B %d at %I:%M %p'))
                    event.setStartString(date, '%A, %B %d at %I:%M %p%Y')

                # Remove scripts
                self.removeScriptsFromElement(eventHtml)

                description = eventHtml.get_text()
                description = self.replaceWhitespaceWithPipes(description)
                event.setDescription(description)

                self.addEvent(event)
            except Exception as e:
                eventText = self.replaceWhitespaceWithPipes(eventHtml.get_text())
                logger.exception("Exception occurred in " + eventText)

        return self
