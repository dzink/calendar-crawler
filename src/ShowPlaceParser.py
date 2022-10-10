import re
from Event import Event
from CalendarParser import CalendarParser
from CalendarLogger import logger

class ShowPlaceParser(CalendarParser):

    """
    Set the post offset to select which post to parse. 0 parses the latest, 1
    the second latest, etc.
    """
    def setPostOffset(self, postOffset):
        self.postOffset = postOffset

    def parseEvents(self, settings = {}):
        post = self.soup().find_all('div', class_='post-content')
        bodyText = post[self.postOffset].find('div', class_='body-text')
        date = False



        for element in bodyText.findChildren():
            if (element.name == 'h2'):
                date = element.text
            if (element.name == 'p'):
                text = element.text
                if (text):
                    # Scraping magic happens here
                    parsed = re.findall("(.*)(\\.\\s+)((1?\\d)(:\\d\\d)?(AM|PM))?.*?,?\\s+((\\$?.*)\\s+)?\\@\\s+(.*)", text)

                    if (parsed):
                        event = Event()
                        event.setSummary(parsed[0][0])
                        event.setLocation(parsed[0][8])
                        event.setDescription(self.replaceWhitespaceWithPipes(text))
                        event.setStartString(self.buildStartstamp(date, parsed), '%A, %B %d, %Y %I:%M%p')
                        event.setEndString(self.buildEndstamp(date), '%A, %B %d, %Y %I:%M%p')
                        self.addEvent(event)

                    else:
                        logger.warning('Could not parse: `' + text + '` for ' + date)

        return self

    def buildStartstamp(self, date, parsed):
        hours = parsed[0][3]
        minutes = parsed[0][4]
        pm = parsed[0][5]
        if (minutes == ''):
            minutes = ':00'

        if (hours == ''):
            time = time = '{date} 12:00AM'.format(date = date)
        else:
            time = '{date} {hours}{minutes}{pm}'.format(
                date = date,
                hours = hours,
                minutes = minutes,
                pm = pm,
            )

        return time

    def buildEndstamp(self, date):
        time = '{date} 11:59PM'.format(date = date)
        return time
