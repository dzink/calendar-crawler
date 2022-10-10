import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleCalendarBuilder:
    credentialsFile = 'data/credentials.json'
    tokenFile = 'data/token.json'
    scopes = ['https://www.googleapis.com/auth/calendar.events']

    def __init__(self):
        self.serviceObject = None

    def service(self):
        if (self.serviceObject == None):
            self.serviceObject = build('calendar', 'v3', credentials = self.getCreds())
        return self.serviceObject

    def setScopes(self, newScopes):
        this.scopes = newScopes
        return self

    def getCalendarIdFromFile(self, file):
        calendarId = ''
        with open(file, 'r') as token:
            calendarId = token.read().replace("\n", '')
            token.close()
        return calendarId

    def syncEvent(self, event, calendarId):
        try:
            if (event.skipSync != True):
                calendarEventId = None
                eventData = self.getDictionaryFromEvent(event)
                if (event.calendarId == None):
                    gEvent = self.service().events().insert(calendarId = calendarId, body = eventData).execute()
                    event.setCalendarId(gEvent['id'])
                else:
                    self.service().events().update(calendarId = calendarId, eventId = event.calendarId, body = eventData).execute()
            else:
                print('skipped')
        except HttpError as error:
            print('An error occurred: %s' % error)
            return None

    def deleteEvent(self, event, calendarId):
        try:
            self.service().events().delete(calendarId = calendarId, eventId = event.calendarId).execute()
            event.setCalendarId(None)
            print(['deleted', event])
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
                creds = flow.run_local_server(port=34242)
            # Save the credentials for the next run
            with open(self.tokenFile, 'w') as token:
                token.write(creds.to_json())
                token.close()

        return creds
