import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from CalendarLogger import logger

class GoogleCalendarBuilder:
    port = 34242
    credentialsFile = 'data/credentials.json'
    tokenFile = 'data/token.json'
    scopes = ['https://www.googleapis.com/auth/calendar.events']

    colorIds = {
        'default': 0,
        'lavender': 1,
        'sage': 2,
        'grape': 3,
        'flamingo': 4,
        'banana': 5,
        'tangerine': 6,
        'peacock': 7,
        'graphite': 8,
        'blueberry': 9,
        'basil': 10,
        'tomato': 11,
    }

    def __init__(self):
        self.serviceObject = None

    def service(self):
        if (self.serviceObject == None):
            self.serviceObject = build('calendar', 'v3', credentials = self.getCreds())
            logger.debug('connected to google calendar')
        return self.serviceObject

    def setScopes(self, newScopes):
        this.scopes = newScopes
        return self

    def getCalendarIdFromFile(self, file):
        calendarId = ''
        with open(file, 'r') as token:
            calendarId = token.read().replace("\n", '')
            token.close()
            logger.debug('retrieved calendar id from file ' + file)
        return calendarId

    def syncEvent(self, event, calendarId):
        try:
            eventData = self.getDictionaryFromEvent(event)
            if (event.skipSync != True):
                calendarEventId = None
                logger.debug('syncing event to calendar ' + str(eventData))

                if (event.calendarId == None):
                    gEvent = self.service().events().insert(calendarId = calendarId, body = eventData).execute()
                    event.setCalendarId(gEvent['id'])
                    logger.debug('new calendar event created with id ' + event.calendarId)

                else:
                    self.service().events().update(calendarId = calendarId, eventId = event.calendarId, body = eventData).execute()
                    logger.debug('existing calendar event updated with id ' + str(event.calendarId))
            else:
                logger.debug('skipping sync of event to calendar ' + str(eventData))

        except HttpError as error:
            print('An error occurred: %s' % error)
            return None

    def dryRun(self, event):
        data = self.getDictionaryFromEvent(event)
        if (event.skipSync):
            logger.info('Dry Run: Skipping ' + str(data))
        else:
            logger.info('Dry Run: Syncing ' + str(data))

    def deleteEvent(self, event, calendarId):
        try:
            self.service().events().delete(calendarId = calendarId, eventId = event.calendarId).execute()
            event.setCalendarId(None)
        except HttpError as error:
            print('An error occurred: %s' % error)
            return None

    def getDictionaryFromEvent(self, event):
        eventData = {}
        eventData['summary'] = event.summary or 'Event'
        eventData['description'] = event.description or ''
        eventData['location'] = event.location or ''
        eventData['source.url'] = event.link or ''
        eventData['source.title'] = event.sourceTitle or ''
        eventData['start'] = {'dateTime': event.startToString()}
        eventData['end'] = {'dateTime': event.endToString()}
        if (event.color != None):
            eventData['colorId'] = self.mapColor(event.color) or 0

        return eventData

    def getCreds(self):
        creds = None

        if os.path.exists(self.tokenFile):
            creds = Credentials.from_authorized_user_file(self.tokenFile, self.scopes)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentialsFile, self.scopes)
                creds = flow.run_local_server(port = self.port)

            # Save the credentials for the next run
            with open(self.tokenFile, 'w') as token:
                token.write(creds.to_json())
                token.close()

        return creds

    def mapColor(self, color):
        lowerColor = str(color).lower()
        return self.colorIds.get(lowerColor)
