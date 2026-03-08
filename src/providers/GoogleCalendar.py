import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from CalendarProvider import CalendarProvider
from CalendarLogger import logger

class GoogleCalendar(CalendarProvider):
    port = 34242

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

    def __init__(self, providerId, config=None):
        super().__init__(providerId, config)
        self.serviceObject = None
        self.googleCalendarId = config.get('googleCalendarId') if config else None
        self.tokenFile = config.get('tokenFile', 'data/token.json') if config else 'data/token.json'
        self.scopes = config.get('scopes', ['https://www.googleapis.com/auth/calendar.events']) if config else ['https://www.googleapis.com/auth/calendar.events']
        self.applicationCredentials = config.get('applicationCredentials') if config else None

    def service(self):
        if (self.serviceObject == None):
            self.serviceObject = build('calendar', 'v3', credentials = self.getCreds())
            logger.debug('connected to google calendar')
        return self.serviceObject

    def addEvent(self, event):
        """Insert an event into Google Calendar. Returns the Google event ID."""
        eventData = self.getDictionaryFromEvent(event)
        logger.info('Inserting event \"%s\" from source \"%s\"' % (event.summary, event.sourceTitle))
        gEvent = self.service().events().insert(calendarId=self.googleCalendarId, body=eventData).execute()
        return gEvent['id']

    def updateEvent(self, event, externalId):
        """Update an existing event on Google Calendar."""
        eventData = self.getDictionaryFromEvent(event)
        logger.info('Updating event \"%s\" from source \"%s\"' % (event.summary, event.sourceTitle))
        self.service().events().update(calendarId=self.googleCalendarId, eventId=externalId, body=eventData).execute()

    def deleteEvent(self, externalId):
        """Delete an event from Google Calendar."""
        self.service().events().delete(calendarId=self.googleCalendarId, eventId=externalId).execute()
        logger.info('Deleted event %s from Google Calendar' % externalId)

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

        eventData['description'] += "\n\nAdministrative note: this Google Calendar is deprecated in favor of a more open source approach that will support many calendar types (including a direct Google Calendar replacement). Support for this calendar may end without notice. Sorry for the hassle. See https://shows.whomtube.com to get the new calendar."
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
                flow = InstalledAppFlow.from_client_config(
                    self.applicationCredentials, self.scopes)
                creds = flow.run_local_server(port = self.port)

            # Save the credentials for the next run
            with open(self.tokenFile, 'w') as token:
                token.write(creds.to_json())
                token.close()

        return creds

    def mapColor(self, color):
        lowerColor = str(color).lower()
        return self.colorIds.get(lowerColor)
