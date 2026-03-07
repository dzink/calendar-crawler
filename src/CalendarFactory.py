"""
CalendarFactory

Orchestrates the full pipeline: parse HTML → transform fields → build events → process.
Instantiates Parser, Transformer, and Processor classes from config (with sensible defaults).
"""

import sys

sys.path.append('./parsers')
sys.path.append('./transformers')
sys.path.append('./processors')

from GoogleCalendar import GoogleCalendar
from CalendarSource import CalendarSource
from Event import Event
from EventList import EventList
from parsers.Parser import Parser
from parsers.ShowPlaceParser import ShowPlaceParser
from transformers.Transformer import Transformer
from processors.Processor import Processor

from CalendarLogger import logger


class CalendarFactory:

    def __init__(self, options, config):
        self.options = options
        self.config = config

    def source(self, sourceId, sourceConfig):
        sourceConfig = sourceConfig['source']
        class_ = sourceConfig.get('class', 'CalendarSource')
        scrollCount = sourceConfig.get('scrollCount', 0)
        url = sourceConfig['url']

        sourceClass = self.getClass(class_)
        source = sourceClass(url, sourceId, self.options.remote, self.config.get('chromeDriverLocation', None), self.config.get('chromeBinaryLocation', None))

        if scrollCount:
            source.setScrollCount(scrollCount)

        return source

    def parser(self, sourceId, sourceConfig):
        parserConfig = sourceConfig.get('parser', {})
        name = sourceConfig.get('name')
        class_ = parserConfig.get('class', 'Parser')

        parserClass = self.getClass(class_)
        return parserClass(name, parserConfig)

    def transformer(self, sourceConfig):
        config = sourceConfig.get('transform', {})
        if isinstance(config, list):
            return Transformer(), config
        class_ = config.get('class', 'Transformer')
        steps = config.get('steps', [])
        cls = self.getClass(class_)
        return cls(), steps

    def processor(self, sourceConfig):
        config = sourceConfig.get('process', {})
        if isinstance(config, list):
            return Processor(), config
        class_ = config.get('class', 'Processor')
        steps = config.get('steps', [])
        cls = self.getClass(class_)
        return cls(), steps

    def buildEvents(self, fieldsList, sourceTitle):
        """Convert a list of transformed field dicts into an EventList."""
        events = EventList([])
        for fields in fieldsList:
            event = Event()
            event.setSourceTitle(sourceTitle)
            if fields.get('title'):
                event.setSummary(fields['title'])
            if fields.get('description'):
                event.setDescription(fields['description'])
            if fields.get('link'):
                event.setLink(fields['link'])
            if fields.get('location'):
                event.setLocation(fields['location'])
            if fields.get('img'):
                event.setImg(fields['img'], fields.get('imgAlt'))
            if fields.get('start'):
                event.setStartString(fields['start'], fields.get('startFormat', '%Y-%m-%d %H:%M'))
            if fields.get('end'):
                event.setEndString(fields['end'], fields.get('endFormat', '%Y-%m-%d %H:%M'))
            events.add(event)
        return events

    def getEvents(self, html, sourceId, sourceConfig):
        """Run the full pipeline: parse → transform → build → process."""
        name = sourceConfig.get('name', sourceId)

        # Parse: extract raw field dicts from HTML
        parser = self.parser(sourceId, sourceConfig)
        logger.debug('parsing beginning for ' + name)
        fieldsList = list(parser.parseFields(html))
        logger.debug('parsing completed for ' + name)

        # Transform: transform each field dict
        transformer, transformSteps = self.transformer(sourceConfig)
        if transformSteps:
            fieldsList = [transformer.run(fields, transformSteps) for fields in fieldsList]

        # Build: convert field dicts to Event objects
        events = self.buildEvents(fieldsList, name)
        logger.info('%d events found in %s' % (len(events.events), name))

        # Process: filter, annotate, etc.
        processor, processSteps = self.processor(sourceConfig)
        if processSteps:
            events = processor.run(events, processSteps)

        return events

    def googleCalendar(self, calendarConfig, secrets={}):
        googleCalendar = GoogleCalendar()
        googleApiConfig = calendarConfig.get('googleApi', {})
        calendarIdSecretKey = googleApiConfig.get('calendarIdSecretKey')
        if calendarIdSecretKey:
            calendarId = secrets.get(calendarIdSecretKey)
            googleCalendar.calendarId = calendarId
            logger.debug('Got calendarId from secrets file')

        applicationCredentialsSecretKey = googleApiConfig.get('applicationCredentialsSecretKey')
        if applicationCredentialsSecretKey:
            applicationCredentials = secrets.get(applicationCredentialsSecretKey)
            googleCalendar.applicationCredentials = applicationCredentials
            logger.debug('Got application credentials from secrets file')

        scopes = googleApiConfig.get('scopes')
        if scopes:
            googleCalendar.scopes = scopes

        tokenFile = googleApiConfig.get('tokenFile')
        if tokenFile:
            googleCalendar.tokenFile = tokenFile

        return googleCalendar

    def getClass(self, class_):
        return getattr(sys.modules[__name__], class_)
