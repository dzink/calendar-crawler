"""
CalendarPipeline

Runs the per-source event pipeline (fetch → parse → transform → build →
process → deduplicate) and the sync loop (write changed events to DB,
queue changes to external calendars).
"""

from EventList import EventList
from CalendarItemsDb import CalendarItemsDb
from CalendarLogger import logger


class CalendarPipeline:

    def __init__(self, factory, options):
        self.factory = factory
        self.options = options
        self.calendarItemsDb = CalendarItemsDb()

    def getEvents(self, sourceId, sourceConfig):
        """Run the full pipeline for one source. Returns an EventList."""
        try:
            name = sourceConfig.get('name', sourceId)

            # Fetch
            fetcher = self.factory.fetcher(sourceId, sourceConfig)
            html = fetcher.getHtml()

            # Parse
            parser = self.factory.parser(sourceId, sourceConfig)
            fieldsList = list(parser.parseFields(html))

            # Transform
            transformer, transformSteps = self.factory.transformer(sourceConfig)
            if transformSteps:
                fieldsList = [transformer.run(fields, transformSteps) for fields in fieldsList]

            # Build
            events = self.factory.buildEvents(fieldsList, name)
            logger.info('%d events found in %s' % (len(events.events), name))

            # Process
            processor, processSteps = self.factory.processor(sourceConfig)
            if processSteps:
                events = processor.run(events, processSteps)

            # Deduplicate
            for event in events:
                event.deduplicate(forceUpdateIfMatched=self.options.force_update)

            return events

        except Exception as e:
            logger.exception("Exception occurred in source " + sourceId)
            return EventList()

    def sync(self, events, calendarId):
        """Write events to DB and queue changes for external calendars.
        Returns (inserted, updated, skipped)."""
        inserted = 0
        updated = 0
        skipped = 0

        for event in events:
            if event.skipSync:
                skipped += 1
            else:
                if event.isDuplicate:
                    updated += 1
                else:
                    inserted += 1
                if not self.options.dry_run:
                    event.write()
                    logger.info('Written: %s' % event.summary)

        if not self.options.dry_run:
            self.calendarItemsDb.upsertSyncStatus(events, calendarId)

        return inserted, updated, skipped
