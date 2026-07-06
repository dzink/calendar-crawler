import os
from icalendar import Calendar, Event as ICalEvent
from CalendarLogger import logger
from Config import Config


def buildIcalEvent(event):
    """Build a single ICalEvent from an Event, with flyer/link prepended to description."""
    ical_event = ICalEvent()
    ical_event.add('uid', str(event.id))
    estimated = getattr(event, 'timeIsEstimated', False)
    ical_event.add('summary', event.summary or '')
    if event.startDate:
        ical_event.add('dtstart', event.startDate)
    if event.endDate:
        ical_event.add('dtend', event.endDate)
    if event.location:
        ical_event.add('location', event.location)
    desc_parts = []
    if event.link:
        desc_parts.append(event.link)
        ical_event.add('url', event.link)
    if event.urlTicket:
        desc_parts.append('Ticket link: %s' % event.urlTicket)
    if event.urlRsvp:
        desc_parts.append('RSVP link: %s' % event.urlRsvp)
    if event.img:
        desc_parts.append('Flyer: %s' % event.img)
        ical_event.add('attach', event.img, parameters={'FMTTYPE': 'image/jpeg'})
    if event.description:
        desc_parts.append(event.description)
    if estimated:
        desc_parts.append('* Time may be estimated based on typical source data; be sure to confirm before heading out.')
    desc_parts.append('See https://shows.whomtube.com for more.')
    ical_event.add('description', '\n\n'.join(desc_parts))
    return ical_event


def buildCalendar(events):
    """Build a single icalendar Calendar containing all events."""
    cal = Calendar()
    cal.add('prodid', '-//Calendar Crawler//EN')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'Baltimore DIY Calendar Crawler')

    for event in events:
        cal.add_component(buildIcalEvent(event))
        logger.info('Added: %s (%s)' % (event.summary, event.startToString('%Y-%m-%d')))

    return cal


def writeCalendar(cal, output_path):
    """Write an icalendar Calendar object to disk."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'wb') as f:
        f.write(cal.to_ical())

    logger.info('Wrote %s' % output_path)


def getSourceList(events):
    """Return list of (source_key, source_name, count) without writing files."""
    sources = Config().loadSources()

    name_to_key = {cfg['name']: key for key, cfg in sources.items()}

    by_source = {}
    for event in events:
        title = event.sourceTitle
        if title:
            by_source.setdefault(title, []).append(event)

    source_list = []
    for source_name, source_events in sorted(by_source.items()):
        source_key = name_to_key.get(source_name)
        if not source_key:
            continue
        source_list.append((source_key, source_name, len(source_events)))

    return source_list


def writeSourceCalendars(events, output_dir):
    """Write one ICS file per source (e.g. ottobar.ics, showPlace.ics)."""
    sources = Config().loadSources()

    name_to_key = {cfg['name']: key for key, cfg in sources.items()}

    by_source = {}
    for event in events:
        title = event.sourceTitle
        if title:
            by_source.setdefault(title, []).append(event)

    for source_name, source_events in sorted(by_source.items()):
        source_key = name_to_key.get(source_name)
        if not source_key:
            logger.warning('No source key found for "%s", skipping ICS' % source_name)
            continue

        cal = Calendar()
        cal.add('prodid', '-//Calendar Crawler//EN')
        cal.add('version', '2.0')
        cal.add('x-wr-calname', 'Baltimore DIY Calendar Crawler - %s' % source_name)

        for event in source_events:
            cal.add_component(buildIcalEvent(event))

        ics_path = os.path.join(output_dir, '%s.ics' % source_key)
        with open(ics_path, 'wb') as f:
            f.write(cal.to_ical())
        logger.info('Wrote %s (%d events)' % (ics_path, len(source_events)))
