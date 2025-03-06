import re
from Event import Event
from CalendarParser import CalendarParser
from CalendarLogger import logger

class ShowPlaceParser(CalendarParser):

    """
    Set the post offset to select which post to parse. 0 parses the latest, 1
    the second latest, etc.
    """
    def setPostOffsets(self, postOffsets):
        self.postOffsets = postOffsets

    def parseEvents(self, html, settings = {}):
        post = self.soup(html).find_all('div', class_='post-content')

        if (self.postOffsets is None):
            self.postOffsets = [0]

        for offset in self.postOffsets:
            bodyText = post[offset].find('div', class_='body-text')
            date = False
            logger.info('Capturing most recent post %d in ShowPlace' % (offset + 1))
            for element in bodyText.findChildren():
                if (element.name == 'h2'):
                    date = element.text
                if (element.name == 'p'):
                    text = element.text
                    if (text):

                        # Scraping magic happens here
                        text = self.replaceWhitespace(text, ' ')
                        try:
                            event = self.parseWaterfall(text, date)
                            if (event):
                                self.addEvent(event)
                            else:
                                logger.warning('Could not parse: `' + text + '` for ' + date)
                        except Exception as e:
                            logger.exception("Exception occurred in %s for date %s" % (text, date))

        return self

    """
    Parse a number of options for malformed items
    """
    def parseWaterfall(self, text, date):
        event = Event()
        event.setDescription(self.replaceWhitespaceWithPipes(text))

        # Default
        venueParsed = re.findall('(.*)\\s*\\@\\s*([^@]*)$', text)
        if (not venueParsed):
            return None
        event.setLocation(venueParsed[0][1])
        text = venueParsed[0][0]

        summaryParsed = re.findall('\\s*(.*)\\.\\s*([^.]*)\\s*$', text)
        if (summaryParsed):
            event.setSummary(summaryParsed[0][0])
            text = summaryParsed[0][1]
        else:
            event.setSummary(text)

        time = self.parseStartAndEndTimesFromFuzzyString(text)
        if (time[0]):
            start_time = time[0]
        else:
            start_time = "7:00pm"

        event.setStartString('{date} {time}'.format(
            date = date,
            time = (time[0] or '7:00pm'),
        ), '%A, %B %d, %Y %I:%M%p')
        event.setEndString('{date} {time}'.format(
            date = date,
            time = (time[1] or '11:59pm'),
        ), '%A, %B %d, %Y %I:%M%p')

        return event
