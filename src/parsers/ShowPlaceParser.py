import re
from Event import Event
from CalendarParser import CalendarParser
from CalendarLogger import logger

class ShowPlaceParser(CalendarParser):

    def setPostOffset(self, postOffset):
        """
        Set the post offset to select which post to parse. 0 parses the latest, 1
        the second latest, etc.
        """
        self.postOffset = postOffset

    def parseEvents(self, html, settings = {}):
        post = self.soup(html).find_all('div', class_='post-content')
        bodyText = post[self.postOffset].find('div', class_='body-text')
        date = False

        for element in bodyText.findChildren():
            if (element.name == 'h2'):
                date = element.text
            if (element.name == 'p'):
                text = element.text
                if (text):

                    # Scraping magic happens here
                    text = self.replaceWhitespace(text, ' ')
                    parsed = self.parseWaterfall(text)

                    if (parsed):
                        try:
                            event = Event()
                            event.setSummary(parsed[0][0])
                            event.setLocation(parsed[0][8])
                            event.setDescription(self.replaceWhitespaceWithPipes(text))
                            event.setStartString(self.buildStartstamp(date, parsed), '%A, %B %d, %Y %I:%M%p')
                            event.setEndString(self.buildEndstamp(date), '%A, %B %d, %Y %I:%M%p')
                            self.addEvent(event)

                        except Exception as e:
                            logger.exception("Exception occurred in %s for date %s" % (text, date))

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

    """
    Parse a number of options for malformed items
    """
    def parseWaterfall(self, text):
        # Default
        parsed = re.findall("(.*?)(\\.|\\?|!|,)\\s+((1?\\d)(:\\d\\d)?(AM|PM)).*?,?\\s+((\\$?.*?)\\s+)?\\@\\s*(.*)", text)

        if (parsed):
            return parsed

        # No ending period
        parsed = re.findall("(.*?)(,)?\\s+((1?\\d)(:\\d\\d)?(AM|PM)).*?,?\\s+((\\$?.*?)\\s+)?\\@\\s*(.*)", text)

        if (parsed):
            return parsed

        # No @
        parsed = re.findall("(.*?)(\\.|\\?|!|,)\\s+((1?\\d)(:\\d\\d)?(AM|PM)).*?,?\\s+((\\$?.*?)\\s+)?\\s*(.*)", text)

        if (parsed):
            return parsed


        return None
