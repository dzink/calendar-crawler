"""Shared string manipulation utilities used by Parser and Transformer."""

import re


def replaceWhitespace(text, replacement=' | '):
    if text is None:
        return text
    text = re.sub(r'(^\s+)|(\s+$)', '', text)
    text = re.sub(r'((\s){2,})|\n', replacement, text)
    return text


def replaceWhitespaceWithPipes(text):
    return replaceWhitespace(text, ' | ')


def removeOrdinalsFromNumbersInString(text):
    matches = re.findall(r'(.*)(\dst|\dnd|\drd|\dth)(.*)', text)
    if matches:
        text = '%s%s%s' % (matches[0][0], matches[0][1][0], matches[0][2])
    return text


def parseStartAndEndTimesFromFuzzyString(string):
    """Parse start and end times from fuzzy strings like '7-9pm', 'doors at 8', 'noon'.
    Returns [startTime, endTime] where each is a string like '7:00pm' or None."""
    startTime = None
    endTime = None

    timeMatch = re.findall(
        r'((noon|((\d+?):?(\d\d)?))\s*((am|pm)?\s*(-|to)\s*(\d+?):?(\d\d)?)?\s*(am|pm))',
        string, re.IGNORECASE
    )

    if not timeMatch:
        timeMatch = re.findall(
            r'doors (at|@) (noon|((\d?)(:\d\d)?))\s*(((((fff)))))?(am|pm)?',
            string, re.IGNORECASE
        )

    if timeMatch:
        timeMatch = timeMatch[0]

        if timeMatch[1].lower() == 'noon':
            startTime = "12:00pm"
        else:
            startTime = "%s:%s%s" % (timeMatch[3], timeMatch[4] or '00', timeMatch[6] or timeMatch[10] or 'pm')

        if timeMatch[8]:
            endTime = "%s:%s%s" % (timeMatch[8], timeMatch[9] or '00', timeMatch[10] or 'pm')

    return [startTime, endTime]
