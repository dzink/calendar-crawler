"""
Processor

Config-driven event list processing. Runs after all events are built,
operating on the full EventList (filtering, etc).

See PARSER_CONFIG.md in the project root for full documentation.
"""

import re
from EventList import EventList
from CalendarLogger import logger


class Processor:

    def run(self, events, steps):
        """Run all process steps on an EventList. Returns the modified list."""
        for step in steps:
            events = self._dispatch(events, step)
        return events

    def _dispatch(self, events, step):
        t = step.get('type')

        if t == 'rejectEvents':
            return self._rejectEvents(events, step)

        raise Exception('Unknown process type: %s' % t)

    # --- Process types ---

    def _rejectEvents(self, events, step):
        criteria = step.get('pattern')
        selected = EventList()
        for event in events:
            if not event.matches(criteria, regex=True):
                selected.add(event)
        return selected
