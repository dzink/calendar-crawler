from CalendarParser import CalendarParser
from Event import Event
from CalendarLogger import logger
from dateutil.parser import parse as dateutil_parse
from datetime import timedelta
import re
import copy


class GenericParser(CalendarParser):

    acceptsConfig = True

    def __init__(self, sourceTitle, parserConfig=None):
        super().__init__(sourceTitle)
        self.parserConfig = parserConfig or {}

    def parseEvents(self, html, settings={}):
        config = self.parserConfig
        fieldDefs = config.get('fields', {})
        tamperDefs = config.get('tamper', [])

        soup = self.soup(html)

        for el, extra in self.collectElements(soup, config):
            try:
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

    def collectElements(self, soup, config):
        """Yield (element, extra_fields) for each item to parse. Override in subclasses."""
        container = config.get('container')
        require = config.get('require')
        elements = self._select(soup, container)
        for el in elements:
            if require and not el.select_one(require):
                continue
            yield el, {}

    def beforeTamper(self, fields):
        """Called after field extraction, before tamper pipeline. Override in subclasses."""
        return fields

    def afterTamper(self, fields):
        """Called after tamper pipeline, before event creation. Override in subclasses."""
        return fields

    def _buildEvent(self, fields):
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
            event.setStartString(fields['start'], fields['startFormat'])
        if fields.get('end'):
            event.setEndString(fields['end'], fields['endFormat'])

        self.addEvent(event)

    def _select(self, soup, selector):
        """Parse a selector string into a BeautifulSoup find operation."""
        if not selector:
            return []
        return soup.select(selector)

    def _extractField(self, el, defn):
        """Extract a field value from an element based on its definition."""
        if defn is None:
            return None

        # Simple string shorthand: "h1.title" or "a@href" or "img@src | img@data-src"
        if isinstance(defn, str):
            return self._extractShorthand(el, defn)

        # Object form with selector, extract options, etc.
        selector = defn.get('selector')
        separator = defn.get('separator', ', ')

        if defn.get('all') and selector:
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

        # Auto-detect description fields
        if 'description' in shorthand.lower() or shorthand == 'description':
            return self.getDescriptionText(target)

        return target.get_text().strip()

    def _extractValue(self, target, extract):
        """Extract a value from an element based on extract type."""
        if extract == 'text':
            return target.get_text().strip()
        if extract == 'description':
            return self.getDescriptionText(target)
        if extract.startswith('attr:'):
            return target.get(extract[5:])
        return target.get_text().strip()

    def _tamper(self, fields, step):
        """Apply a tamper step to the field bag."""
        t = step.get('type')

        if t == 'parseDate':
            return self._tamperParseDate(fields, step)
        if t == 'parseDateFuzzy':
            return self._tamperParseDateFuzzy(fields, step)
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
        if t == 'join':
            return self._tamperJoin(fields, step)
        if t == 'append':
            return self._tamperAppend(fields, step)
        if t == 'autoDate':
            return self._tamperAutoDate(fields, step)

        logger.warning('Unknown tamper type: %s' % t)
        return fields

    def _tamperParseDate(self, fields, step):
        """Concatenate fields and store as a date string with format."""
        source_fields = step.get('fields', [])
        fmt = step.get('format')
        target = step.get('target', 'start')
        separator = step.get('separator', '')

        parts = [str(fields.get(f, '')) for f in source_fields]
        dateStr = separator.join(parts)

        fields[target] = dateStr
        fields[target + 'Format'] = fmt
        return fields

    def _tamperParseDateFuzzy(self, fields, step):
        """Parse date with fuzzy time extraction, setting both start and end."""
        source_fields = step.get('fields', [])
        fmt = step.get('format')
        defaultTime = step.get('defaultTime', '19:00')
        defaultEndTime = step.get('defaultEndTime')
        separator = step.get('separator', ' ')

        timeField = step.get('timeField', 'time')
        timeValue = fields.get(timeField, '')
        times = self.parseStartAndEndTimesFromFuzzyString(timeValue) if timeValue else [None, None]

        startTime = times[0]
        endTime = times[1]

        if not startTime:
            h, m = defaultTime.split(':')
            startTime = '%s:%s%s' % (str(int(h) % 12 or 12), m, 'am' if int(h) < 12 else 'pm')

        if not endTime and defaultEndTime:
            h, m = defaultEndTime.split(':')
            endTime = '%s:%s%s' % (str(int(h) % 12 or 12), m, 'am' if int(h) < 12 else 'pm')

        dateFields = [f for f in source_fields if f != timeField]
        dateParts = [str(fields.get(f, '')) for f in dateFields]
        dateStr = separator.join(dateParts)

        fields['start'] = (dateStr + separator + startTime).strip()
        fields['startFormat'] = fmt

        if endTime:
            fields['end'] = (dateStr + separator + endTime).strip()
            fields['endFormat'] = fmt

        return fields

    def _tamperNearestYear(self, fields, step):
        """Add nearest year to a date field."""
        target = step.get('target', 'date')
        fmt = step.get('format', '%A %B %d')
        value = fields.get(target, '')
        if not value:
            return fields

        event = Event()
        year = event.getNearestYear(value, fmt)
        separator = step.get('separator', '')
        fields[target] = value + separator + str(year)
        return fields

    def _tamperRegex(self, fields, step):
        """Extract or transform a field with a regex."""
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
            # If default matches a field name, use that field's value
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

    def _tamperAutoDate(self, fields, step):
        """Parse date automatically using dateutil with fuzzy time extraction.

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

        # Pre-clean the date text for dateutil
        cleaned = self._cleanDateText(dateText)

        # Parse the date portion
        try:
            dt = dateutil_parse(cleaned, fuzzy=True)
        except (ValueError, OverflowError):
            logger.warning('autoDate: could not parse "%s"' % dateText)
            return fields

        # Apply start time: explicit field > dateutil-extracted > fuzzy > default
        if explicitStartTime:
            dt = self._applyTimeString(dt, explicitStartTime)
        elif dt.hour == 0 and dt.minute == 0:
            if fuzzyStartTime:
                dt = self._applyTimeString(dt, fuzzyStartTime)
            elif defaultTime:
                h, m = defaultTime.split(':')
                dt = dt.replace(hour=int(h), minute=int(m))

        # Nearest year
        event = Event()
        year = event.getNearestYear(dt.strftime('%b %d'), '%b %d')
        dt = dt.replace(year=int(year))

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
        """Pre-clean date text for dateutil parsing."""
        # Remove ordinals: 8th -> 8
        text = re.sub(r'(\d)(st|nd|rd|th)\b', r'\1', text)
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
