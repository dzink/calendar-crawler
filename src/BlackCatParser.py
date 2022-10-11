import re
from CalendarParser import CalendarParser
from Event import Event
from CalendarLogger import logger

class BlackCatParser(CalendarParser):

    location = 'Black Cat DC'

    def parseEvents(self, settings = {}):
        for eventHtml in self.soup().find_all('div', class_ = 'show'):
            h1Html = eventHtml.find('h1')
            link = h1Html.find('a')
            if (link):
                description = eventHtml.get_text()

                link = link.get('href')

                # title = ''
                titles = eventHtml.find_all(['h1', 'h2'])
                title = self.getTitle(titles)

                dateHtml = eventHtml.find('h2', class_ = 'date')
                date = dateHtml.get_text()

                time = re.findall('(\d+)(:\d\d)', description)[0]

                event = Event()

                event.setSummary(title)
                event.setLocation(self.location)
                event.setLink(link)
                event.setDescription(self.replaceWhitespaceWithPipes(description))

                event.setStartString(self.buildStartstamp(date, time), '%A %B %d %Y %I:%M%p')
                event.setAbsoluteEndDateTime(23, 59)

                self.addEvent(event)

        return self

    def buildStartstamp(self, date, timePattern):
        return "%s 2022 %s%sPM" % (date, timePattern[0], timePattern[1] or ':00')

    def getTitle(self, titles):
        strings = []
        for title in titles:
            if (title.name == 'h1'):
                strings.append(title.get_text())

            if (title.name == 'h2' and title['class'][0] == 'support'):
                strings.append(title.get_text())
        return ', '.join(strings)
