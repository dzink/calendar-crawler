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
                event = Event()
                description = eventHtml.get_text()

                link = link.get('href')

                # title = ''
                titles = eventHtml.find_all(['h1', 'h2'])
                title = self.getTitle(titles)

                dateHtml = eventHtml.find('h2', class_ = 'date')
                date = dateHtml.get_text()
                year = event.getNearestYear(date, '%A %B %d')

                time = re.findall('(\d+)(:\d\d)', description)[0]


                event.setSummary(title)
                event.setLocation(self.location)
                event.setLink(link)
                event.setDescription(self.replaceWhitespaceWithPipes(description))
                event.setStartString(self.buildStartstamp(year, date, time), '%A %B %d %Y %I:%M%p')
                event.setAbsoluteEndDateTime(23, 59)

                self.addEvent(event)

        return self

    def buildStartstamp(self, year, date, timePattern):
        return "%s %s %s%sPM" % (date, year, timePattern[0], timePattern[1] or ':00')

    def getTitle(self, titles):
        strings = []
        for title in titles:
            if (title.name == 'h1'):
                strings.append(title.get_text())

            if (title.name == 'h2' and title['class'][0] == 'support'):
                strings.append(title.get_text())
        return ', '.join(strings)
