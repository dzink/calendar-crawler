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
import paths

import os
import re
import shutil
import argparse
from datetime import date
from EventList import EventList

from CalendarLogger import logger, addLoggerArgsToParser, buildLogger
from IcsExporter import buildCalendar, writeCalendar, getSourceList, writeSourceCalendars
from HtmlBuilder import buildHtml, buildFaq
from Assets import compileSass, minifyCss, CSS_OUTPUT, ASSETS_SRC

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
            htmlContent = buildHtml(events, source_list, options.base_url, options.dev)
            writeHtml(htmlContent, options.html)

            faqContent = buildFaq(source_list, options.base_url, options.dev)
            faq_path = os.path.join(os.path.dirname(options.html), 'faq', 'index.html')
            os.makedirs(os.path.dirname(faq_path), exist_ok=True)
            with open(faq_path, 'w') as f:
                f.write(faqContent)
            logger.info('Wrote %s' % faq_path)

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

    # Compile SCSS to CSS (+ source map in dev mode)
    css_dest = os.path.join(assets_dest, CSS_OUTPUT)
    os.makedirs(os.path.dirname(css_dest), exist_ok=True)

    if options.dev:
        css, source_map = compileSass(source_map=True, output_path=css_dest)
        with open(css_dest, 'w') as f:
            f.write(css)
        with open(css_dest + '.map', 'w') as f:
            f.write(source_map)
    else:
        css = compileSass()
        with open(css_dest, 'w') as f:
            f.write(minifyCss(css))

    # Remove SCSS sources — CSS is compiled above, sources don't belong in dist
    scss_dest = os.path.join(assets_dest, 'scss')
    if os.path.isdir(scss_dest):
        shutil.rmtree(scss_dest)

    # Clean up JS source files in prod (JS is inlined in HTML)
    if not options.dev:
        js_dest = os.path.join(assets_dest, 'js')
        if os.path.isdir(js_dest):
            shutil.rmtree(js_dest)

    logger.info('Wrote %s' % output_path)


if __name__ == '__main__':
    main()
