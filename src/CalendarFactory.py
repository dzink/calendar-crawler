""" Factory for different calendar objects used in this project. """

import sys

sys.path.append('./parsers')

from GoogleCalendar import GoogleCalendar
from CalendarSource import CalendarSource
from CalendarParser import CalendarParser
from BlackCatParser import BlackCatParser
from ShowPlaceParser import ShowPlaceParser
from OttobarParser import OttobarParser
from SquareSpaceParser import SquareSpaceParser
from WithFriendsParser import WithFriendsParser
from RhizomeParser import RhizomeParser
from EventList import EventList

from CalendarLogger import logger

class CalendarFactory:

    def __init__(self, options):
        self.options = options

    def source(self, sourceId, config):
        """ Create and configure a source. """
        sourceConfig = config['source']
        class_ = sourceConfig.get('class',  'CalendarSource')
        scrollCount = sourceConfig.get('scrollCount',  0)
        url = sourceConfig['url']

        sourceClass = self.getClassFromString(class_)
        source = sourceClass(url, sourceId, self.options.remote)

        if (scrollCount):
            source.setScrollCount(scrollCount)

        return source

    def parser(self, sourceId, config):
        """ Create and configure a parser. """
        parserConfig = config.get('parser', {})
        name = config.get('name')
        class_ = parserConfig.get('class')
        postOffset = parserConfig.get('postOffset', None)

        parserClass = self.getClassFromString(class_)
        parser = parserClass(name)

        if (postOffset != None):
            parser.setPostOffset(postOffset)

        return parser

    def postTasks(self, events, config):
        """ Find tasks to run on events.

        These tasks are run on every event in the events list.

        events -- an EventList.
        """
        postTasksConfig = config.get('postTasks', [])
        for taskConfig in postTasksConfig:
            events = self.postTask(events, taskConfig)
        return events

    def postTask(self, events, taskConfig):
        """ Run a task on events.

        These tasks are run on every event in the events list.

        events -- an EventList.
        """

        type = taskConfig.get('type')

        if (type == 'addBoilerplateToDescriptions'):
            text = taskConfig.get('text')
            events.addBoilerplateToDescriptions(text)
            return events

        if (type == 'prefixDescriptionsWithLinks'):
            events.prefixDescriptionsWithLinks()
            return events

        if (type == 'rejectEvents'):
            pattern = taskConfig.get('pattern')
            events = events.rejectEvents(pattern)
            return events

        if (type == 'setLocationAddress'):
            text = taskConfig.get('text')
            events.setLocationAddress(text)
            return events

        if (type == 'prefixLinks'):
            text = taskConfig.get('text')
            events.prefixLinks(text)
            return events

        if (type == 'setColors'):
            color = taskConfig.get('color')
            events.setColors(color)
            return events

        if (type == 'setAbsoluteEndDateTime'):
            hour = int(taskConfig.get('hour', 23))
            minute = int(taskConfig.get('minute', 59))
            events.setAbsoluteEndDateTime(hour, minute)
            return events

        raise Exception('Unknown postTask type: %s' % (type))

    def googleCalendar(self, calendarConfig, secrets = {}):
        """ Create and configure a parser. """

        googleCalendar = GoogleCalendar()
        googleApiConfig = calendarConfig.get('googleApi', {})
        calendarIdSecretKey = googleApiConfig.get('calendarIdSecretKey')
        if (calendarIdSecretKey):
            calendarId = secrets.get(calendarIdSecretKey)
            googleCalendar.calendarId = calendarId
            logger.info('Got calendarId from secrets file')

        applicationCredentialsSecretKey = googleApiConfig.get('applicationCredentialsSecretKey')
        if (applicationCredentialsSecretKey):
            applicationCredentials = secrets.get(applicationCredentialsSecretKey)
            googleCalendar.applicationCredentials = applicationCredentials
            logger.info('Got application credentials from secrets file')

        scopes = googleApiConfig.get('scopes')
        if (scopes):
            googleCalendar.scopes = scopes

        tokenFile = googleApiConfig.get('tokenFile')
        if (tokenFile):
            googleCalendar.tokenFile = tokenFile

        return googleCalendar


    def getClassFromString(self, class_):
        """ Converts a string into a class """
        return getattr(sys.modules[__name__], class_)
