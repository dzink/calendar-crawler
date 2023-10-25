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
from GreedyReadsParser import GreedyReadsParser
from RedRoomParser import RedRoomParser
from EventList import EventList

from CalendarLogger import logger

class CalendarFactory:

    def __init__(self, options):
        self.options = options

    def source(self, sourceId, config):
        sourceConfig = config['source']
        class_ = sourceConfig.get('class',  'CalendarSource')
        scrollCount = sourceConfig.get('scrollCount',  0)
        url = sourceConfig['url']

        sourceClass = self.getClass(class_)
        source = sourceClass(url, sourceId, self.options.remote)

        if (scrollCount):
            source.setScrollCount(scrollCount)

        return source

    def parser(self, sourceId, config):
        parserConfig = config.get('parser', {})
        name = config.get('name')
        class_ = parserConfig.get('class')
        postOffsets = parserConfig.get('postOffsets', None)

        parserClass = self.getClass(class_)
        parser = parserClass(name)

        if (postOffsets != None):
            parser.setPostOffsets(postOffsets)

        return parser

    def postTasks(self, events, config):
        postTasksConfig = config.get('postTasks', [])
        for taskConfig in postTasksConfig:
            events = self.postTask(events, taskConfig)
        return events

    def postTask(self, events, taskConfig):
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

        if (type == 'setDefaultTimeLength'):
            hour = int(taskConfig.get('hour', 2))
            minute = int(taskConfig.get('minute', 0))
            events.setDefaultTimeLength(hour, minute)
            return events

        raise Exception('Unknown postTask type: %s' % (type))

    def googleCalendar(self, calendarConfig, secrets = {}):
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


    def getClass(self, class_):
        return getattr(sys.modules[__name__], class_)
