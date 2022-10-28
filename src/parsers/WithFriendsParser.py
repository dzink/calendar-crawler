from CalendarParser import CalendarParser
from Event import Event

class WithFriendsParser(CalendarParser):

    def parseEvents(self, html, settings = {}):
        for eventHtml in self.soup(html).find_all('li', class_='wf-event'):
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
            date = date + str(event.getNearestYear(date, '%A, %B %d at %I:%M %p'))
            event.setStartString(date, '%A, %B %d at %I:%M %p%Y')

            # Remove scripts
            self.removeScriptsFromElement(eventHtml)

            description = eventHtml.get_text()
            description = self.replaceWhitespaceWithPipes(description)
            event.setDescription(description)

            self.addEvent(event)

        return self
