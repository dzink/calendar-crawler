# from bs4 import BeautifulSoup
import re
# import pytz
# from datetime import datetime
from CalendarParser import CalendarParser
from Event import Event

class WithFriendsParser(CalendarParser):

    def parseEvents(self, postOffset = 0):
        for eventHtml in self.soup().find_all('li', class_='wf-event'):
            event = Event()

            link = eventHtml.find('a')
            event.setLink(link.get('href'))

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
            self.removeScripts(eventHtml)

            description = eventHtml.get_text()
            description = re.sub('(^\s+)|(\s+$)', '', description)
            description = re.sub('((\s){2,})|\n', ' | ', description)
            event.setDescription(description)

            self.addEvent(event)

        return self
