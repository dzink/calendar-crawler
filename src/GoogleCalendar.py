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

    def setScopes(self, newScopes):
        this.scopes = newScopes
        return self

    def dryRun(self, event, externalId=None):
        data = self.getDictionaryFromEvent(event)
        if externalId:
            logger.info('Dry run - Updating event \"%s\" on %s from source \"%s\"' % (event.summary, event.startDate, event.sourceTitle))
            logger.debug('Dry Run: Updating ' + str(data))
        else:
            logger.info('Dry run - Inserting event \"%s\" on %s from source \"%s\"' % (event.summary, event.startDate, event.sourceTitle))
            logger.debug('Dry Run: Inserting ' + str(data))

    def syncPending(self, dryRun=False, limit=None):
        """Sync all pending events to Google Calendar. Returns count of synced events."""
        synced = 0
        pending = self.getPendingEvents()
        if limit:
            pending = pending[:limit]
        for event, record in pending:
            externalId = record.get('externalId')
            if dryRun:
                self.dryRun(event, externalId)
                synced += 1
                continue
            try:
                eventData = self.getDictionaryFromEvent(event)

                if externalId:
                    logger.info('Updating event \"%s\" from source \"%s\"' % (event.summary, event.sourceTitle))
                    self.service().events().update(calendarId=self.googleCalendarId, eventId=externalId, body=eventData).execute()
                else:
                    logger.info('Inserting event \"%s\" from source \"%s\"' % (event.summary, event.sourceTitle))
                    gEvent = self.service().events().insert(calendarId=self.googleCalendarId, body=eventData).execute()
                    externalId = gEvent['id']

                self.markSynced(event.id, externalId)
                synced += 1

            except HttpError as error:
                logger.exception("Exception occurred")
                logger.error("The attempted event was: " + str(eventData))

        return synced

    def dryDeleteEvent(self, event):
        logger.info('Dry run - Deleting event \"%s\" on %s from source \"%s\"' % (event.summary, event.startDate, event.sourceTitle))

    def deleteEvent(self, eventId, externalCalendarId):
        """Delete an event from Google Calendar and remove the sync record."""
        try:
            self.service().events().delete(calendarId=self.googleCalendarId, eventId=externalCalendarId).execute()
            logger.info('Deleted event %s from Google Calendar' % eventId)
            self.deleteItem(eventId)

        except HttpError as error:
            logger.exception("Exception occurred")

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

    """
    Get the colorId from the string color name.
    """
    def mapColor(self, color):
        lowerColor = str(color).lower()
        return self.colorIds.get(lowerColor)
