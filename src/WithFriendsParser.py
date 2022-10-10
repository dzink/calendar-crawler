import re
from CalendarParser import CalendarParser
from Event import Event

class WithFriendsParser(CalendarParser):

    def parseEvents(self, settings = {}):
        for eventHtml in self.soup().find_all('li', class_='wf-event'):
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
            # @TODO - get last year, this year, next year, choose whichever is closest to now
            date = date + ' 2022'
            event.setStartString(date, '%A, %B %d at %I:%M %p %Y')

            # Remove scripts
            self.removeScriptsFromElement(eventHtml)

            description = eventHtml.get_text()
            description = self.replaceWhitespaceWithPipes(description)
            event.setDescription(description)

            self.addEvent(event)

        return self
