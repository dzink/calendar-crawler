#!/usr/bin/python
"""
calendar-export.py — Export crawled events to ICS files and an HTML agenda page.

Outputs:
  - dist/<mode>/assets/ics/events.ics   Combined ICS calendar (all events)
  - dist/<mode>/assets/ics/<source>.ics  Per-source ICS calendars
  - dist/<mode>/index.html               Static HTML agenda with:
                                           - date navigation and filtering
                                           - per-event "add to calendar" dropdown
                                             (Google, Outlook, Yahoo, .ics download)
                                           - subscribe links built from --base-url

Modes:
  --dev   Dev build: linked CSS/JS, no minification (dist/dev/)
  default Prod build: inlined & minified CSS/JS (dist/prod/)

Usage:
  python3 calendar-export.py --base-url https://example.com/shows
  python3 calendar-export.py --dev

See EXPORT.md for full documentation.
"""

import sys
sys.path.append('./src')
sys.path.append('./src/parsers')

import os
import re
import html
import yaml
import shutil
import subprocess
import argparse
from datetime import date
from collections import OrderedDict
from icalendar import Calendar, Event as ICalEvent
from EventList import EventList
from datetime import datetime


from CalendarLogger import logger, addLoggerArgsToParser, buildLogger

options = None

def main():
    """Entry point. Builds HTML first (which wipes dist/assets/), then writes
    ICS files so they aren't deleted by the asset copy."""
    try:
        global options
        options = parseArguments()
        buildLogger(options)

        parameters = buildQuery()
        events = EventList().find(parameters)
        logger.info('Found %d events to export' % len(events.events))

        # Collect source metadata without writing files (needed for HTML links)
        source_list = getSourceList(events)

        # HTML must be written first — writeHtml() does shutil.rmtree on
        # dist/assets/ before copying template assets
        if options.html and options.html != 'none':
            htmlContent = buildHtml(events, source_list)
            writeHtml(htmlContent, options.html)

        # ICS files written after HTML so they survive the asset copy
        cal = buildCalendar(events)
        writeCalendar(cal, options.output)

        output_dir = os.path.dirname(options.output) or '.'
        writeSourceCalendars(events, output_dir)

    except Exception as e:
        logger.exception("Exception occurred")


def parseArguments():
    parser = argparse.ArgumentParser(description='Export events to an ICS file')
    addLoggerArgsToParser(parser, {})
    parser.add_argument('-s', '--source', help='Only export events from the given source(s).', action='append', default=None)
    parser.add_argument('-o', '--output', help='Output file path.', default='./dist/assets/ics/events.ics')
    parser.add_argument('-a', '--after', help='Only events after date (YYYY-MM-DD).', default=None)
    parser.add_argument('-b', '--before', help='Only events before date (YYYY-MM-DD).', default=None)
    parser.add_argument('--html', help='Output path for HTML agenda (use "none" to skip).', default='./dist/index.html')
    parser.add_argument('--base-url', help='Base URL for meta tags (e.g. https://example.com/shows).', default='https://shows-dist.sludgefree.workers.dev/')
    parser.add_argument('--dev', action='store_true', default=False, help='Dev build: linked CSS/JS, no minification.')

    args = parser.parse_args()

    # Apply mode-based default paths unless the user gave explicit overrides
    if args.html == './dist/index.html' and args.output == './dist/assets/ics/events.ics':
        mode_dir = 'dev' if args.dev else 'prod'
        args.html = './dist/%s/index.html' % mode_dir
        args.output = './dist/%s/assets/ics/events.ics' % mode_dir

    return args


def buildQuery():
    """Build EventList query from CLI args. Defaults to today onward."""
    parameters = {}
    if options.source:
        parameters['sourceTitle'] = '|'.join(options.source)
    parameters['after'] = options.after or date.today().isoformat()
    if options.before:
        parameters['before'] = options.before
    return parameters


def buildIcalEvent(event):
    """Build a single ICalEvent from an Event, with flyer/link prepended to description."""
    ical_event = ICalEvent()
    ical_event.add('uid', str(event.id))
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
    if event.img:
        desc_parts.append('Flyer: %s' % event.img)
        ical_event.add('attach', event.img, parameters={'FMTTYPE': 'image/jpeg'})
    if event.description:
        desc_parts.append(event.description)
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
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sources.yml')) as f:
        sources = yaml.safe_load(f)

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
    """Write one ICS file per source (e.g. ottobar.ics, showPlace.ics).
    Source keys come from data/sources.yml."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sources.yml')) as f:
        sources = yaml.safe_load(f)

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


def buildDataAttrs(ev):
    """Return a string of data-* attributes for an event's <details> tag."""
    attrs = []
    if ev.startDate:
        attrs.append('data-start="%s"' % ev.startDate.strftime('%Y-%m-%dT%H:%M:%S'))
    if ev.endDate:
        attrs.append('data-end="%s"' % ev.endDate.strftime('%Y-%m-%dT%H:%M:%S'))
    return ' '.join(attrs)


_BARE_URL = re.compile(r'(https?://[^\s<>\"\']+[^\s<>\"\'.,;:)\]])')
_LINK_SPLIT = re.compile(r'(<a\s[^>]*>.*?</a>)', re.IGNORECASE | re.DOTALL)
_A_OPEN = re.compile(r'<a\s', re.IGNORECASE)

def linkify(text):
    """Wrap bare URLs in anchor tags and ensure all links open in new tabs."""
    parts = _LINK_SPLIT.split(text)
    for i, part in enumerate(parts):
        if _LINK_SPLIT.match(part):
            if 'target=' not in part:
                parts[i] = _A_OPEN.sub('<a target="_blank" ', part)
        else:
            parts[i] = _BARE_URL.sub(r'<a href="\1" target="_blank" rel="noopener">\1</a>', part)
    return ''.join(parts)


def buildHtml(events, source_list=None):
    """Build the full HTML string for the agenda page.

    Groups events by day into <section> elements, renders each event as a
    <details> with data-* attributes for the add-to-cal JS, and substitutes
    all {{placeholders}} in the HTML template including subscribe links
    derived from --base-url.
    """
    # Group events by date
    days = OrderedDict()
    for event in events:
        if not event.startDate:
            continue
        key = event.startDate.strftime('%Y-%m-%d')
        days.setdefault(key, []).append(event)

    sorted_keys = sorted(days.keys())

    # Rotate the week grid so column 1 is the weekday of the first event
    first_weekday = days[sorted_keys[0]][0].startDate.strftime('%w') if sorted_keys else 0
    first_weekday = int(first_weekday)

    sections = []
    for day_key in sorted_keys:
        day_events = sorted(days[day_key], key=lambda e: e.startDate)
        date_obj = day_events[0].startDate
        heading = date_obj.strftime('%A, %B ') + str(date_obj.day)

        items = []
        for ev in day_events:
            summary = html.escape(ev.summary or 'Untitled')
            time_str = ev.startDate.strftime('%-I:%M %p') if ev.startDate else ''
            approx_end = ev.description and re.search(r'End times? (?:is|are) approximate', ev.description, re.IGNORECASE)
            location = html.escape(ev.location) if ev.location else ''
            link = html.escape(ev.link) if ev.link else ''
            source = html.escape(ev.sourceTitle) if ev.sourceTitle else ''
            meta_parts = []
            if time_str:
                meta_parts.append(time_str + ('*' if approx_end else ''))
            if location:
                meta_parts.append('at ' + location)
            # if source:
            #     meta_parts.append('from source ' + source)
            meta_line = '<span class="summary-meta">%s</span>' % ' &middot; '.join(meta_parts) if meta_parts else ''
            summary_line = '<span class="summary-text">%s%s</span>' % (summary, meta_line)

            detail_lines = []
            if ev.startDate and ev.endDate:
                time_range = '%s – %s%s' % (ev.startDate.strftime('%-I:%M %p'), ev.endDate.strftime('%-I:%M %p'), '*' if approx_end else '')
                detail_lines.append('<div class="time time-range">%s</div>' % html.escape(time_range))
            elif ev.startDate:
                detail_lines.append('<div class="time">%s</div>' % html.escape(ev.startDate.strftime('%-I:%M %p')))
            if location:
                detail_lines.append('<div class="location">%s</div>' % location)
            if link:
                detail_lines.append(linkify('<div class="link-url"><a href="%s" title="%s">%s</a></div>' % (link, summary, link)))
            flyer = ev.flyerHtml()
            if flyer:
                detail_lines.append(flyer)
            if ev.description:
                # data-desc marks this div so JS can grab its textContent
                # for calendar descriptions
                paragraphs = re.split(r'\n+', ev.description.strip())
                desc_html = ''.join('<p>%s</p>' % linkify(p) for p in paragraphs if p.strip())
                detail_lines.append('<div data-desc class="description">%s</div>' % desc_html)
            # if ev.link:
                # detail_lines.append('<a href="%s" target="_blank" rel="noopener">Event Link</a>' % html.escape(ev.link))
            # data-* attrs on <details> carry event info for client-side calendar URLs
            data_attrs = buildDataAttrs(ev)
            items.append(
                '<details %s>'
                '<summary>%s</summary>'
                '<div class="details">%s</div>'
                '</details>' % (data_attrs, summary_line, ''.join(detail_lines))
            )

        weekday_col = (int(date_obj.strftime('%w')) - first_weekday) % 7 + 1
        sections.append(
            '<section id="day-%s" style="grid-column:%d">'
            '<h2 tabindex="-1">%s</h2>'
            '%s'
            '</section>' % (day_key, weekday_col, heading, ''.join(items))
        )

    source_ics_html = ''
    if source_list:
        source_links = []
        for key, name, count in source_list:
            source_links.append(
                '<li><a href="assets/ics/%s.ics">%s</a> <span>%d events</span></li>' % (
                    html.escape(key), html.escape(name), count))
        source_ics_html = ''.join(source_links)

    # Build subscribe URLs from --base-url for webcal, Google, Outlook, Office365
    base_url = options.base_url.rstrip('/')
    https_ics = base_url + '/assets/ics/events.ics'
    webcal_ics = https_ics.replace('https://', 'webcal://', 1)
    name = 'Baltimore DIY Calendar Crawler'
    encoded_name = html.escape(name, quote=True).replace(' ', '%20')

    result = HTML_TEMPLATE.replace('{{content}}', ''.join(sections))
    result = result.replace('{{year}}', str(datetime.now().year))
    result = result.replace('{{source_ics_links}}', source_ics_html)
    result = result.replace('{{base_url}}', base_url)
    result = result.replace('{{webcal_ics}}', webcal_ics)
    result = result.replace('{{google_ics}}', 'https://calendar.google.com/calendar/r?cid=%s' % webcal_ics)
    result = result.replace('{{outlook_ics}}', 'https://outlook.live.com/calendar/0/addfromweb?url=%s&name=%s' % (https_ics, encoded_name))
    result = result.replace('{{office365_ics}}', 'https://outlook.office.com/calendar/0/addfromweb?url=%s&name=%s' % (https_ics, encoded_name))
    if options.dev:
        result = result.replace('{{styles}}', linkCss())
        result = result.replace('{{scripts}}', linkJs())
    else:
        result = result.replace('{{styles}}', inlineCss())
        result = result.replace('{{scripts}}', inlineJs())
    return result


ASSETS_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'html-template/assets')
TEMPLATE_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'html-template')

with open(os.path.join(TEMPLATE_SRC, 'index.html')) as f:
    HTML_TEMPLATE = f.read()

CSS_FILES = ['css/minimal.css']

def inlineCss():
    """Read CSS files and return a single minified <style> block."""
    parts = []
    for name in CSS_FILES:
        with open(os.path.join(ASSETS_SRC, name)) as f:
            parts.append(minifyCss(f.read()))
    return '<style>' + ''.join(parts) + '</style>'

def linkCss():
    """Return <link> tags pointing to external CSS files (for dev builds)."""
    return '\n'.join('<link rel="stylesheet" href="assets/%s">' % name for name in CSS_FILES)

JS_FILES = ['js/agenda.js']

def inlineJs():
    """Read JS files and return a single minified <script> block."""
    parts = []
    for name in JS_FILES:
        with open(os.path.join(ASSETS_SRC, name)) as f:
            parts.append(minifyJs(f.read()))
    return '<script>' + ''.join(parts) + '</script>'

def linkJs():
    """Return <script src> tags pointing to external JS files (for dev builds)."""
    return '\n'.join('<script src="assets/%s"></script>' % name for name in JS_FILES)

def minifyCss(text):
    """Naive CSS minifier: strip comments, collapse whitespace, remove
    unnecessary spaces around punctuation."""
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s*([{}:;,>~+])\s*', r'\1', text)
    text = re.sub(r';}', '}', text)
    return text.strip()

UGLIFYJS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'node_modules/.bin/uglifyjs')

def minifyJs(text):
    """Minify JS with uglify-js if available, otherwise fall back to naive minifier."""
    if os.path.isfile(UGLIFYJS):
        try:
            result = subprocess.run(
                [UGLIFYJS, '--compress', '--mangle'],
                input=text, capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
            logger.warning('uglifyjs failed: %s' % result.stderr.strip())
        except Exception as e:
            logger.warning('uglifyjs unavailable: %s' % e)
    return _naiveMinifyJs(text)

def _naiveMinifyJs(text):
    """Fallback: strip // line comments and /* block comments */,
    then collapse blank lines. WARNING: this will destroy // inside string
    literals — use String.fromCharCode(47, 47) instead."""
    text = re.sub(r'//.*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return '\n'.join(lines)

def writeHtml(htmlContent, output_path):
    """Write the HTML file and copy template assets to dist/assets/.

    WARNING: This deletes and re-copies dist/assets/, so any files written
    there before this call (e.g. ICS files) will be lost. The main() function
    accounts for this by writing ICS files after writeHtml().
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    if not options.dev:
        htmlContent = re.sub(r'<!--.*?-->', '', htmlContent, flags=re.DOTALL)

    with open(output_path, 'w') as f:
        f.write(htmlContent)

    # Replace dist/assets/ with a fresh copy from html-template/assets/
    assets_dest = os.path.join(output_dir, 'assets')
    if os.path.isdir(assets_dest):
        shutil.rmtree(assets_dest)
    shutil.copytree(ASSETS_SRC, assets_dest)

    # Minify the copied asset files in-place (skip in dev mode)
    if not options.dev:
        for root, dirs, files in os.walk(assets_dest):
            for name in files:
                path = os.path.join(root, name)
                if name.endswith('.css'):
                    with open(path) as f:
                        original = f.read()
                    with open(path, 'w') as f:
                        f.write(minifyCss(original))
                elif name.endswith('.js'):
                    with open(path) as f:
                        original = f.read()
                    with open(path, 'w') as f:
                        f.write(minifyJs(original))

    logger.info('Wrote %s' % output_path)


if __name__ == '__main__':
    main()
