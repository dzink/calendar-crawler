"""
GenericParser

A config-driven event parser. All parsing behavior is defined in sources.yml
using CSS selectors for field extraction and a tamper pipeline for transformations.

Subclasses can override three hooks:
  - collectElements(): controls which HTML elements become events
  - beforeTamper(): transforms fields after extraction, before the tamper pipeline
  - afterTamper(): transforms fields after tampers, before event creation

See PARSER_CONFIG.md in the project root for full config syntax documentation.
"""

from CalendarParser import CalendarParser
from Event import Event
from CalendarLogger import logger
import dateparser
from dateutil.parser import parse as dateutil_parse
from datetime import timedelta
import re
import copy


class GenericParser(CalendarParser):

    # When True, CalendarFactory passes the parser config dict to __init__.
    acceptsConfig = True

    def __init__(self, sourceTitle, parserConfig=None):
        super().__init__(sourceTitle)
        self.parserConfig = parserConfig or {}

    def parseEvents(self, html, settings=None):
        """Main parse loop: collect elements, extract fields, run tampers, build events."""
        config = self.parserConfig
        fieldDefs = config.get('fields', {})
        tamperDefs = config.get('tamper', [])

        soup = self.makeSoup(html)

        for el, extra in self.collectElements(soup, config):
            try:
                # Extract fields from the element, seeded with any extra fields
                # provided by collectElements (e.g. a date heading)
                fields = dict(extra)
                for name, defn in fieldDefs.items():
                    fields[name] = self._extractField(el, defn)

                fields = self.beforeTamper(fields)

                for step in tamperDefs:
                    fields = self._tamper(fields, step)

                fields = self.afterTamper(fields)

                self._buildEvent(fields)
            except Exception as e:
                eventText = self.replaceWhitespaceWithPipes(el.get_text())
                logger.exception("Exception occurred in " + eventText)

        return self

    # --- Subclass hooks ---

    def collectElements(self, soup, config):
        """Yield (element, extra_fields) for each item to parse.
        Override in subclasses to change how events are collected from the page."""
        container = config.get('container')
        require = config.get('require')
        elements = self._select(soup, container)
        for el in elements:
            if require and not el.select_one(require):
                continue
            yield el, {}

    def beforeTamper(self, fields):
        """Hook called after field extraction, before tamper pipeline."""
        return fields

    def afterTamper(self, fields):
        """Hook called after tamper pipeline, before event creation."""
        return fields

    # --- Event building ---

    def _buildEvent(self, fields):
        """Map the processed field bag to an Event object and add it to the list."""
        event = Event()
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

        self.addEvent(event)

    # --- Field extraction ---
    # Fields are defined in sources.yml and can be either shorthand strings
    # or object definitions. See PARSER_CONFIG.md for the full syntax.

    def _select(self, soup, selector):
        if not selector:
            return []
        return soup.select(selector)

    def _extractField(self, el, defn):
        """Extract a field value from an element based on its definition.
        Supports shorthand strings ("h2", "a@href", "img@src | img@data-src")
        and object form with selector, extract, index, all, fallback, etc."""
        if defn is None:
            return None

        # Simple string shorthand: "h1.title" or "a@href" or "img@src | img@data-src"
        if isinstance(defn, str):
            return self._extractShorthand(el, defn)

        # Object form with selector, extract options, etc.
        selector = defn.get('selector')
        separator = defn.get('separator', ', ')

        select = defn.get('select', 'first')

        if select == 'all' and selector:
            targets = el.select(selector)
            if not targets:
                return defn.get('default')
            extract = defn.get('extract', 'text')
            parts = [self._extractValue(t, extract) for t in targets]
            return separator.join(p for p in parts if p)

        index = defn.get('index')
        if index is not None and selector:
            targets = el.select(selector)
            target = targets[index] if len(targets) > index else None
        else:
            target = el.select_one(selector) if selector else el

        if target is None:
            return defn.get('default')

        removeTag = defn.get('removeTag')
        if removeTag:
            target = copy.copy(target)
            self.removeTagFromElement(target, removeTag)

        extract = defn.get('extract', 'text')
        value = self._extractValue(target, extract)

        if value is None:
            fallback = defn.get('fallback')
            if fallback:
                return self._extractField(el, fallback)
            return defn.get('default')

        return value

    def _extractShorthand(self, el, shorthand):
        """Parse shorthand like 'h1.title', 'a@href', 'img@src | img@data-src'."""
        # Pipe = fallback chain
        if ' | ' in shorthand:
            for part in shorthand.split(' | '):
                result = self._extractShorthand(el, part.strip())
                if result:
                    return result
            return None

        # @ = attribute extraction
        if '@' in shorthand:
            selector, attr = shorthand.rsplit('@', 1)
            target = el.select_one(selector) if selector else el
            if target is None:
                return None
            return target.get(attr)

        # Bare selector = text extraction
        target = el.select_one(shorthand)
        if target is None:
            return None

        return target.get_text().strip()

    def _extractValue(self, target, extract):
        """Extract a value from an element based on extract type."""
        if extract == 'text':
            return target.get_text().strip()
        if extract == 'paragraphs':
            return self.getDescriptionText(target)
        if extract.startswith('attr:'):
            return target.get(extract[5:])
        return target.get_text().strip()

    # --- Tamper pipeline ---
    # Tampers are ordered processing steps that transform the extracted field bag
    # before the event is created. Each step operates on the shared fields dict.

    def _tamper(self, fields, step):
        """Dispatch a tamper step to the appropriate handler."""
        t = step.get('type')

        if t == 'nearestYear':
            return self._tamperNearestYear(fields, step)
        if t == 'regex':
            return self._tamperRegex(fields, step)
        if t == 'replace':
            return self._tamperReplace(fields, step)
        if t == 'prefix':
            return self._tamperPrefix(fields, step)
        if t == 'removeOrdinals':
            return self._tamperRemoveOrdinals(fields, step)
        if t == 'collapseWhitespace':
            return self._tamperCollapseWhitespace(fields, step)
        if t == 'collapseParagraphs':
            return self._tamperCollapseParagraphs(fields, step)
        if t == 'cut':
            return self._tamperCut(fields, step)
        if t == 'copy':
            return self._tamperCopy(fields, step)
        if t == 'join':
            return self._tamperJoin(fields, step)
        if t == 'append':
            return self._tamperAppend(fields, step)
        if t == 'autoDate':
            return self._tamperAutoDate(fields, step)

        logger.warning('Unknown tamper type: %s' % t)
        return fields

    def _tamperNearestYear(self, fields, step):
        """Add nearest year to a date field."""
        target = step.get('target', 'date')
        fmt = step.get('format', '%A %B %d')
        value = fields.get(target, '')
        if not value:
            return fields

        year = Event.getNearestYear(value, fmt)
        separator = step.get('separator', '')
        fields[target] = value + separator + str(year)
        return fields

    def _tamperRegex(self, fields, step):
        """Extract or transform a field with a regex.
        If the pattern doesn't match, 'default' can be a literal value
        or the name of another field to copy from."""
        target = step.get('target')
        pattern = step.get('pattern')
        group = step.get('group', 0)
        store = step.get('store', target)
        value = fields.get(target, '')

        if not value:
            return fields

        match = re.search(pattern, value)
        if match:
            fields[store] = match.group(group)
        elif 'default' in step:
            default = step['default']
            if default in fields:
                fields[store] = fields[default]
            else:
                fields[store] = default

        return fields

    def _tamperReplace(self, fields, step):
        """String find/replace on a field."""
        target = step.get('target')
        find = step.get('find', '')
        replace = step.get('replace', '')
        value = fields.get(target, '')
        if value:
            if step.get('regex'):
                fields[target] = re.sub(find, replace, value)
            else:
                fields[target] = value.replace(find, replace)
        return fields

    def _tamperPrefix(self, fields, step):
        """Prepend text to a field, with optional regex guard."""
        target = step.get('target')
        text = step.get('text', '')
        unless = step.get('unless')
        value = fields.get(target, '')

        if value and (not unless or not re.search(unless, value)):
            fields[target] = text + value
        return fields

    def _tamperRemoveOrdinals(self, fields, step):
        """Strip ordinal suffixes from numbers in a field."""
        target = step.get('target')
        value = fields.get(target, '')
        if value:
            fields[target] = self.removeOrdinalsFromNumbersInString(value)
        return fields

    def _tamperCollapseWhitespace(self, fields, step):
        """Collapse whitespace in a field.
        No options: collapse to empty string.
        separator: collapse to given string (e.g. ' ', ' | ').
        trim: only strip leading/trailing whitespace."""
        target = step.get('target')
        value = fields.get(target, '')
        if not value:
            return fields
        if step.get('trim') and 'separator' not in step:
            fields[target] = value.strip()
        else:
            separator = step.get('separator', '')
            fields[target] = self.replaceWhitespace(value, separator)
        return fields

    def _tamperCollapseParagraphs(self, fields, step):
        """Normalize whitespace while preserving paragraph breaks.
        Spaces collapse to single space, newlines collapse to max 2."""
        target = step.get('target')
        value = fields.get(target, '')
        if value:
            value = re.sub(r'[^\S\n]*\n[^\S\n]*', '\n', value)
            value = re.sub(r'\n{3,}', '\n\n', value)
            value = re.sub(r'[^\S\n]{2,}', ' ', value)
            fields[target] = value.strip()
        return fields

    def _tamperCut(self, fields, step):
        """Remove a regex pattern from a field."""
        target = step.get('target')
        pattern = step.get('pattern')
        value = fields.get(target, '')
        if value:
            fields[target] = re.sub(pattern, '', value)
        return fields

    def _tamperCopy(self, fields, step):
        """Copy one field's value to another."""
        target = step.get('target')
        store = step.get('store')
        value = fields.get(target, '')
        if value:
            fields[store] = value
        return fields

    def _tamperJoin(self, fields, step):
        """Concatenate multiple fields into one."""
        source_fields = step.get('fields', [])
        store = step.get('store')
        separator = step.get('separator', '')
        parts = [str(fields.get(f, '')) for f in source_fields if fields.get(f)]
        fields[store] = separator.join(parts)
        return fields

    def _tamperAppend(self, fields, step):
        """Append one field's value onto another with a separator."""
        target = step.get('target')
        field = step.get('field')
        separator = step.get('separator', ', ')
        targetVal = fields.get(target, '')
        fieldVal = fields.get(field, '')
        if targetVal and fieldVal:
            fields[target] = targetVal + separator + fieldVal
        return fields

    # --- autoDate ---
    # The primary date-parsing tamper. Uses dateparser for flexible date parsing
    # and parseStartAndEndTimesFromFuzzyString (from CalendarParser) for extracting
    # start/end times from strings like "7-9pm", "doors at 8", "noon".
    # Time priority: explicit time fields > fuzzy-extracted times > defaults.

    _dateparser_settings = {
        'RETURN_AS_TIMEZONE_AWARE': False,
    }

    def _tamperAutoDate(self, fields, step):
        """Parse date automatically using dateparser with fuzzy time extraction.

        Options:
          target:          field containing date text (default: "date")
          timeField:       optional field with fuzzy time text (e.g. "Doors at 7")
          startTimeField:  optional field with explicit start time (e.g. "7:30 PM")
          endTimeField:    optional field with explicit end time (e.g. "9:30 PM")
          defaultTime:     fallback start time in 24h, e.g. "19:00"
          defaultDuration: fallback end = start + duration, e.g. "2:00" (hours:minutes)
          defaultEndTime:  fallback end = same day at this time, e.g. "22:00" (24h)
        """
        target = step.get('target', 'date')
        timeField = step.get('timeField')
        startTimeField = step.get('startTimeField')
        endTimeField = step.get('endTimeField')
        defaultTime = step.get('defaultTime', '19:00')
        defaultDuration = step.get('defaultDuration')
        defaultEndTime = step.get('defaultEndTime')

        dateText = fields.get(target, '')
        if not dateText:
            return fields

        # Get explicit start/end time fields if provided
        explicitStartTime = fields.get(startTimeField, '').strip() if startTimeField else ''
        explicitEndTime = fields.get(endTimeField, '').strip() if endTimeField else ''

        # Extract fuzzy times from timeField or date text
        fuzzyStartTime = None
        fuzzyEndTime = None
        if timeField:
            timeText = fields.get(timeField, '')
            if timeText:
                fuzzyStartTime, fuzzyEndTime = self.parseStartAndEndTimesFromFuzzyString(timeText)
        elif not explicitStartTime:
            fuzzyStartTime, fuzzyEndTime = self.parseStartAndEndTimesFromFuzzyString(dateText)

        # Pre-clean noisy date text
        cleaned = self._cleanDateText(dateText)

        # Parse the date portion
        dt = dateparser.parse(cleaned, settings=self._dateparser_settings)
        if not dt:
            logger.warning('autoDate: could not parse "%s"' % dateText)
            return fields

        # Detect whether dateparser extracted a time by checking if the
        # cleaned text contains time-like patterns. Midnight (00:00) from
        # dateparser means "no time found" unless the text explicitly says so.
        parsedHasTime = dt.hour != 0 or dt.minute != 0 or bool(
            re.search(r'(?:^|\s)(?:12\s*(?:am|AM|midnight)|00:00)', cleaned))

        # Correct year to nearest (handles yearless dates near year boundary)
        year = Event.getNearestYear(dt.strftime('%b %d'), '%b %d')
        dt = dt.replace(year=int(year))

        # Apply start time: explicit field > dateparser-extracted > fuzzy > default
        if explicitStartTime:
            dt = self._applyTimeString(dt, explicitStartTime)
        elif not parsedHasTime:
            if fuzzyStartTime:
                dt = self._applyTimeString(dt, fuzzyStartTime)
            elif defaultTime:
                h, m = defaultTime.split(':')
                dt = dt.replace(hour=int(h), minute=int(m))

        # Store start
        fields['start'] = dt.strftime('%Y-%m-%d %H:%M')
        fields['startFormat'] = '%Y-%m-%d %H:%M'

        # Determine end: explicit field > fuzzy > defaultDuration > defaultEndTime
        endDt = None
        if explicitEndTime:
            endDt = self._applyTimeString(dt, explicitEndTime)
        elif fuzzyEndTime:
            endDt = self._applyTimeString(dt, fuzzyEndTime)
        elif defaultDuration:
            h, m = defaultDuration.split(':')
            endDt = dt + timedelta(hours=int(h), minutes=int(m))
        elif defaultEndTime:
            h, m = defaultEndTime.split(':')
            endDt = dt.replace(hour=int(h), minute=int(m))

        if endDt:
            fields['end'] = endDt.strftime('%Y-%m-%d %H:%M')
            fields['endFormat'] = '%Y-%m-%d %H:%M'

        return fields

    def _cleanDateText(self, text):
        """Pre-clean noisy date text for parsing."""
        # Remove pipe-separated suffixes (price, etc)
        text = re.sub(r'\s*\|.*', '', text)
        # Replace @ with space (used as time separator)
        text = re.sub(r'\s*@\s*', ' ', text)
        # Remove dash-separated end times: "10:00AM - 10:30 AM" -> "10:00AM"
        text = re.sub(r'\s*-\s+\d{1,2}[:\d]*\s*[AaPp][Mm].*', '', text)
        # Remove asterisks (used as separators in some sources)
        text = text.replace('*', ' ')
        return text.strip()

    def _applyTimeString(self, dt, timeStr):
        """Apply a fuzzy time string like '7:00pm' to a datetime."""
        timeStr = timeStr.replace('::', ':')
        try:
            parsed = dateutil_parse(timeStr)
            return dt.replace(hour=parsed.hour, minute=parsed.minute)
        except (ValueError, OverflowError):
            return dt
