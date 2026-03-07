"""
CalendarFactory

Builds pipeline components from config: Fetcher, Parser, Transformer, Processor.
The caller is responsible for running the pipeline.
"""

import sys

sys.path.append('./parsers')
sys.path.append('./transformers')
sys.path.append('./processors')

from GoogleCalendar import GoogleCalendar
from Fetcher import Fetcher
from Event import Event
from EventList import EventList
from parsers.Parser import Parser
from parsers.ShowPlaceParser import ShowPlaceParser
from transformers.Transformer import Transformer
from processors.Processor import Processor

from CalendarLogger import logger


class CalendarFactory:

    def __init__(self, options, config, secrets=None):
        self.options = options
        self.config = config
        self.secrets = secrets or {}

    def fetcher(self, sourceId, sourceConfig):
        fetchConfig = self.resolveSecrets(sourceConfig.get('fetch', {}), self.secrets)
        return Fetcher(sourceId, fetchConfig, self.options.remote, self.config)

    def parser(self, sourceId, sourceConfig):
        parserConfig = sourceConfig.get('parse', {})
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

    def providers(self, calendarKey, calendarConfig):
        """Build a list of CalendarProvider instances from calendar config."""
        providers = []
        for providerConfig in calendarConfig.get('providers', []):
            type_ = providerConfig.get('type')
            config = self.resolveSecrets(providerConfig, self.secrets)
            if type_ == 'google':
                providers.append(GoogleCalendar(calendarKey, config))
            else:
                logger.warning('Unknown provider type: %s' % type_)
        return providers

    def resolveSecrets(self, config, secrets):
        """Resolve secret references in a config dict. Values like {secret: keyName} are replaced."""
        resolved = {}
        for key, value in config.items():
            if isinstance(value, dict) and 'secret' in value:
                secretKey = value['secret']
                resolved[key] = secrets.get(secretKey)
            else:
                resolved[key] = value
        return resolved

    def getClass(self, class_):
        return getattr(sys.modules[__name__], class_)
