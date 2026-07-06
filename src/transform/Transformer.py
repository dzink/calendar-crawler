"""
Transformer

Config-driven field transformation pipeline. Each step operates on a
shared fields dict, modifying values before events are built.

See PARSER_CONFIG.md in the project root for full documentation.
"""

from Event import Event
from CalendarLogger import logger
import StringUtils
import dateparser
from dateutil.parser import parse as dateutil_parse
from datetime import timedelta
import re


class Transformer:

    def run(self, fields, steps):
        """Run all transform steps on a fields dict. Returns the modified dict."""
        for step in steps:
            fields = self._dispatch(fields, step)
        return fields

    def _dispatch(self, fields, step):
        skipEmpty = step.get('skipEmpty')
        if skipEmpty:
            value = fields.get(skipEmpty if isinstance(skipEmpty, str) else step.get('field', step.get('target', '')), '')
            if not value or not str(value).strip():
                return fields

        for cond_key in ('onlyIf', 'unless'):
            condition = step.get(cond_key)
            if not condition:
                continue
            negate = cond_key == 'unless'
            if isinstance(condition, str):
                value = str(fields.get(step.get('field', step.get('target', '')), '') or '')
                passed = bool(re.search(condition, value))
            else:
                field = condition.get('field') or condition.get('target')
                value = str(fields.get(field, '') or '') if field else self._interpolate(condition.get('value', ''), fields)
                operation = condition.get('operation')
                search = self._interpolate(condition.get('contains') or condition.get('value', ''), fields)
                matches = condition.get('matches')
                exact = condition.get('exact')
                if operation == 'exact':
                    passed = value == self._interpolate(exact, fields)
                elif operation == 'matches':
                    passed = bool(re.search(matches, value))
                elif operation == 'search':
                    passed = search.lower() in value.lower()
                else:
                    passed = bool(value.strip())
            if negate:
                passed = not passed
            if not passed:
                return fields

        for cond_key, want_empty in (('onlyIfEmpty', True), ('onlyIfNotEmpty', False)):
            field = step.get(cond_key)
            if not field:
                continue
            if isinstance(field, dict):
                field = field.get('field', '')
            if not field or not isinstance(field, str):
                logger.warning('Transformer: %s expects a field name string' % cond_key)
                continue
            is_empty = not str(fields.get(field, '') or '').strip()
            if want_empty != is_empty:
                return fields

        t = step.get('type')

        if t == 'nearestYear':
            return self._nearestYear(fields, step)
        if t == 'regex':
            return self._regex(fields, step)
        if t == 'replace':
            return self._replace(fields, step)
        if t == 'prefix':
            return self._prefix(fields, step)
        if t == 'removeOrdinals':
            return self._removeOrdinals(fields, step)
        if t == 'collapseWhitespace':
            return self._collapseWhitespace(fields, step)
        if t == 'collapseParagraphs':
            return self._collapseParagraphs(fields, step)
        if t == 'cut':
            return self._cut(fields, step)
        if t == 'copy':
            return self._copy(fields, step)
        if t == 'join':
            return self._join(fields, step)
        if t == 'append':
            return self._append(fields, step)
        if t == 'set':
            return self._set(fields, step)
        if t == 'autoDate':
            return self._autoDate(fields, step)
        if t == 'autoNotaflof':
            return self._autoNotaflof(fields, step)

        logger.warning('Unknown transform type: %s' % t)
        return fields

    # --- Helpers ---

    def _interpolate(self, text, fields):
        """Replace {fieldName} placeholders with field values."""
        if not isinstance(text, str):
            return text
        def replacer(match):
            key = match.group(1)
            return str(fields.get(key, ''))
        return re.sub(r'\{(\w+)\}', replacer, text)

    # --- Transform types ---

    def _nearestYear(self, fields, step):
        target = step.get('field', step.get('target', 'date'))
        fmt = step.get('format', '%A %B %d')
        value = fields.get(target, '')
        if not value:
            return fields
        year = Event.getNearestYear(value, fmt)
        separator = step.get('separator', '')
        fields[target] = value + separator + str(year)
        return fields

    def _regex(self, fields, step):
        """Extract or transform a field with a regex.
        If the pattern doesn't match, 'default' provides a fallback.
        Use {fieldName} in default to reference another field's value."""
        target = step.get('field', step.get('target'))
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
            fields[store] = self._interpolate(step['default'], fields)

        return fields

    def _replace(self, fields, step):
        target = step.get('field', step.get('target'))
        find = self._interpolate(step.get('find', ''), fields)
        replace = self._interpolate(step.get('replace', ''), fields)
        value = fields.get(target, '')
        if value:
            if step.get('regex'):
                fields[target] = re.sub(find, replace, value)
            else:
                fields[target] = value.replace(find, replace)
        return fields

    def _prefix(self, fields, step):
        target = step.get('field', step.get('target'))
        text = self._interpolate(step.get('text', ''), fields)
        unless = step.get('unless')
        value = fields.get(target, '')
        if value and (not unless or not re.search(unless, value)):
            fields[target] = text + value
        return fields

    def _removeOrdinals(self, fields, step):
        target = step.get('field', step.get('target'))
        value = fields.get(target, '')
        if value:
            fields[target] = StringUtils.removeOrdinalsFromNumbersInString(value)
        return fields

    def _collapseWhitespace(self, fields, step):
        target = step.get('field', step.get('target'))
        value = fields.get(target, '')
        if not value:
            return fields
        if step.get('trim') and 'separator' not in step:
            fields[target] = value.strip()
        else:
            separator = step.get('separator', '')
            fields[target] = StringUtils.replaceWhitespace(value, separator)
        return fields

    def _collapseParagraphs(self, fields, step):
        target = step.get('field', step.get('target'))
        value = fields.get(target, '')
        if value:
            value = re.sub(r'[^\S\n]*\n[^\S\n]*', '\n', value)
            value = re.sub(r'\n{3,}', '\n\n', value)
            value = re.sub(r'[^\S\n]{2,}', ' ', value)
            fields[target] = value.strip()
        return fields

    def _cut(self, fields, step):
        target = step.get('field', step.get('target'))
        pattern = step.get('pattern')
        value = fields.get(target, '')
        if value:
            fields[target] = re.sub(pattern, '', value)
        return fields

    def _copy(self, fields, step):
        target = step.get('field', step.get('target'))
        store = step.get('store')
        value = fields.get(target, '')
        if value:
            fields[store] = value
        return fields

    def _join(self, fields, step):
        source_fields = step.get('fields', [])
        store = step.get('store')
        separator = step.get('separator', '')
        parts = [str(fields.get(f, '')) for f in source_fields if fields.get(f)]
        fields[store] = separator.join(parts)
        return fields

    def _append(self, fields, step):
        target = step.get('field', step.get('target'))
        text = step.get('text', '')
        targetVal = fields.get(target, '')
        fields[target] = (targetVal or '') + self._interpolate(text, fields)
        return fields

    def _set(self, fields, step):
        """Set a field to a value. Use {fieldName} to reference other fields."""
        target = step.get('field', step.get('target'))
        value = step.get('value', '')
        fields[target] = self._interpolate(value, fields) if isinstance(value, str) else value
        return fields

    def _autoNotaflof(self, fields, step):
        """Set isNotaflof if 'notaflof' appears in summary or description."""
        for field in ('title', 'description'):
            if re.search(r'notaflof', fields.get(field, '') or '', re.IGNORECASE):
                fields['isNotaflof'] = True
                return fields
        return fields

    # --- autoDate ---

    _dateparser_settings = {
        'RETURN_AS_TIMEZONE_AWARE': False,
    }

    def _autoDate(self, fields, step):
        """Parse date automatically using dateparser with fuzzy time extraction."""
        target = step.get('field', step.get('target', 'date'))
        timeField = step.get('timeField')
        startTimeField = step.get('startTimeField')
        endTimeField = step.get('endTimeField')
        defaultTime = step.get('defaultTime', '19:00')
        defaultDuration = step.get('defaultDuration')
        defaultEndTime = step.get('defaultEndTime')

        dateText = fields.get(target, '')
        if not dateText:
            return fields

        explicitStartTime = (fields.get(startTimeField) or '').strip() if startTimeField else ''
        explicitEndTime = (fields.get(endTimeField) or '').strip() if endTimeField else ''

        fuzzyStartTime = None
        fuzzyEndTime = None
        if timeField:
            timeText = fields.get(timeField, '')
            if timeText:
                fuzzyStartTime, fuzzyEndTime = StringUtils.parseStartAndEndTimesFromFuzzyString(timeText)
        elif not explicitStartTime:
            fuzzyStartTime, fuzzyEndTime = StringUtils.parseStartAndEndTimesFromFuzzyString(dateText)

        cleaned = self._cleanDateText(dateText)

        dt = dateparser.parse(cleaned, settings=self._dateparser_settings)
        if not dt:
            logger.warning('autoDate: could not parse "%s"' % dateText)
            return fields

        parsedHasTime = dt.hour != 0 or dt.minute != 0 or bool(
            re.search(r'(?:^|\s)(?:12\s*(?:am|AM|midnight)|00:00)', cleaned))

        year = Event.getNearestYear(dt.strftime('%b %d'), '%b %d')
        dt = dt.replace(year=int(year))

        if explicitStartTime:
            dt = self._applyTimeString(dt, explicitStartTime)
        elif not parsedHasTime:
            if fuzzyStartTime:
                dt = self._applyTimeString(dt, fuzzyStartTime)
            elif defaultTime:
                h, m = defaultTime.split(':')
                dt = dt.replace(hour=int(h), minute=int(m))
                fields['timeIsEstimated'] = True

        fields['start'] = dt.strftime('%Y-%m-%d %H:%M')
        fields['startFormat'] = '%Y-%m-%d %H:%M'

        endDt = None
        if explicitEndTime:
            endDt = self._applyTimeString(dt, explicitEndTime)
        elif fuzzyEndTime:
            endDt = self._applyTimeString(dt, fuzzyEndTime)
        elif defaultDuration:
            h, m = defaultDuration.split(':')
            endDt = dt + timedelta(hours=int(h), minutes=int(m))
            fields['timeIsEstimated'] = True
        elif defaultEndTime:
            h, m = defaultEndTime.split(':')
            endDt = dt.replace(hour=int(h), minute=int(m))
            fields['timeIsEstimated'] = True

        if endDt:
            if endDt <= dt:
                endDt += timedelta(days=1)
            fields['end'] = endDt.strftime('%Y-%m-%d %H:%M')
            fields['endFormat'] = '%Y-%m-%d %H:%M'

        return fields

    def _cleanDateText(self, text):
        text = re.sub(r'\s*\|.*', '', text)
        text = re.sub(r'\s*@\s*', ' ', text)
        text = re.sub(r'\s*-\s+\d{1,2}[:\d]*\s*[AaPp][Mm].*', '', text)
        text = text.replace('*', ' ')
        return text.strip()

    def _applyTimeString(self, dt, timeStr):
        timeStr = timeStr.replace('::', ':')
        try:
            parsed = dateutil_parse(timeStr)
            return dt.replace(hour=parsed.hour, minute=parsed.minute)
        except (ValueError, OverflowError):
            return dt
