""" Factory for different calendar objects used in this project. """
# Imports are defined by strings and need to be available here.
# pylint: disable=unused-import

import sys
from GoogleCalendar import GoogleCalendar
from CalendarSource import CalendarSource
from CalendarParser import CalendarParser

sys.path.append('./parsers')

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

    def parser(self, config):
        """ Create and configure a parser. """
        parserConfig = config.get('parser', {})
        name = config.get('name')
        class_ = parserConfig.get('class')
        postOffset = parserConfig.get('postOffset', None)

        parserClass = self.getClassFromString(class_)
        parser = parserClass(name)

        if (postOffset is None):
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
        # pylint: disable=too-many-return-statements

        task_id = taskConfig.get('taskId')

        if (task_id == 'addBoilerplateToDescriptions'):
            text = taskConfig.get('text')
            events.addBoilerplateToDescriptions(text)
            return events

        if (task_id == 'prefixDescriptionsWithLinks'):
            events.prefixDescriptionsWithLinks()
            return events

        if (task_id == 'rejectEvents'):
            pattern = taskConfig.get('pattern')
            events = events.rejectEvents(pattern)
            return events

        if (task_id == 'setLocationAddress'):
            text = taskConfig.get('text')
            events.setLocationAddress(text)
            return events

        if (task_id == 'prefixLinks'):
            text = taskConfig.get('text')
            events.prefixLinks(text)
            return events

        if (task_id == 'setColors'):
            color = taskConfig.get('color')
            events.setColors(color)
            return events

        if (task_id == 'setAbsoluteEndDateTime'):
            hour = int(taskConfig.get('hour', 23))
            minute = int(taskConfig.get('minute', 59))
            events.setAbsoluteEndDateTime(hour, minute)
            return events

        raise Exception('Unknown postTask task_id: %s' % (task_id))

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
