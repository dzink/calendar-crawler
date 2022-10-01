from bs4 import BeautifulSoup
import re
import pytz
from datetime import datetime
from Event import Event
from CalendarParser import CalendarParser

class ShowPlaceParser(CalendarParser):

    def parseEvents(self, postOffset = 0):
        soup = BeautifulSoup(self.html, features="html.parser")

        post = soup.find_all('div', class_='post-content')
        bodyText = post[postOffset].find('div', class_='body-text')
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
                        event.setDescription(text)
                        event.setStartString(self.buildStartstamp(date, parsed), '%A, %B %d, %Y %I:%M%p')
                        event.setEndString(self.buildEndstamp(date), '%A, %B %d, %Y %I:%M%p')
                        self.addEvent(event)

                    else:
                        print('ERROR Could not parse: `' + text + '`')
                    # try:
                    #     event = {
                    #         'summary': parsed[0][0],
                    #         'start': {
                    #             'dateTime': self.buildStartstamp(date, parsed),
                    #             'timeZone': 'US/Eastern',
                    #         },
                    #         'end': {
                    #             'dateTime': self.buildEndstamp(date),
                    #             'timeZone': 'US/Eastern',
                    #         },
                    #         'location': parsed[0][8],
                    #         'description': text,
                    #     }
                    #     self.addEvent(event)
                    # except:
                    #     print('ERROR: ' + text)

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
