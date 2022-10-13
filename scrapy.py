#!/usr/bin/python

import sys
sys.path.append('./src')

import argparse
from EventDb import EventDb
from Event import Event
from EventList import EventList
from GoogleCalendarBuilder import GoogleCalendarBuilder
from CalendarSource import CalendarSource
from CalendarParser import CalendarParser
from BlackCatParser import BlackCatParser
from ShowPlaceParser import ShowPlaceParser
from OttobarParser import OttobarParser
from SquareSpaceParser import SquareSpaceParser
from WithFriendsParser import WithFriendsParser

from time import sleep
from CalendarLogger import logger, addLoggerArgsToParser, buildLogger

options = None

def main():
    try:
        global options
        options = parseArguments()
        buildLogger(options)

        gcb = GoogleCalendarBuilder()
        calendarId = gcb.getCalendarIdFromFile('data/calendarid.txt')

        events = []

        events = events + showPlace().events
        events = events + ottobar().events
        events = events + redEmmas().events
        events = events + currentSpace().events
        events = events + blackCat().events
        events = events + space2640().events
        events = events + joeSquared().events

        for event in events:
            event.deduplicate(forceUpdateIfMatched = options.force_update)
            if (not options.dry_run):
                gcb.syncEvent(event, calendarId)
                event.write()
            else:
                gcb.dryRun(event)

    except Exception as e:
        logger.exception("Exception occurred")

def parseArguments():
    parser = argparse.ArgumentParser(description='Scrape event pages and add them to a Google calendar')
    addLoggerArgsToParser(parser)
    parser.add_argument('-l', '--local', help = 'Whether to use local cached sources instead of re-scraping html.', action = 'store_false', default = True, dest = 'remote')
    parser.add_argument('-u', '--force-update', help = 'Whether to force Google Calendar updates, even if there\'s nothing to update.', action = 'store_true', default = False)
    parser.add_argument('-d', '--dry-run', help = 'Run the parser but do not write to the calendar or database.', action = 'store_true', default = False)

    return parser.parse_args()

def redEmmas():
    source = CalendarSource('https://withfriends.co/red_emmas/events', 'red_emmas', options.remote)
    source.setScrollCount(4)
    html = source.getHtml()

    parser = WithFriendsParser(html, 'Red Emma\'s')
    events = parser.parse().getEventsList()

    events.addBoilerplateToDescriptions('End time is approximate. See https://withfriends.co/red_emmas/events for more.')
    events.prefixDescriptionsWithLinks()
    events.setAbsoluteEndDateTime(22, 00)
    events.setLocationAddress('Red Emma\'s')
    events.setColors('tomato')

    return events

def currentSpace():
    source = CalendarSource('https://withfriends.co/current_space/events', 'current_space', options.remote)
    source.setScrollCount(4)
    html = source.getHtml()

    parser = WithFriendsParser(html, 'Current Space')
    events = parser.parse().getEventsList()

    events.addBoilerplateToDescriptions('End time is approximate. See https://withfriends.co/current_space/events for more.')
    events.prefixDescriptionsWithLinks()
    events.setAbsoluteEndDateTime(22, 30)
    events.setLocationAddress('Current Space')
    events.setColors('banana')

    return events

def showPlace():
    source = CalendarSource('https://baltshowplace.tumblr.com/', 'showplace', options.remote)
    html = source.getHtml()

    parser = ShowPlaceParser(html, 'ShowPlace')
    parser.setPostOffset(0)
    events = parser.parse().getEventsList()

    # Reject events that come from other scraped sources
    events = events.rejectEvents({'location': '(Ottobar|Red Emma\'s|Current Space|2640)'})

    events.addBoilerplateToDescriptions('End times are approximate. See https://baltshowplace.tumblr.com/ for more.')
    events.setColors('sage')

    return events

def ottobar():
    source = CalendarSource('https://theottobar.com/calendar/', 'ottobar', options.remote)
    html = source.getHtml()

    parser = OttobarParser(html, 'Ottobar')
    events = parser.parse().getEventsList()
    events = events.rejectEvents({'location': '(Joe Squared|Current Space)'})
    events.prefixDescriptionsWithLinks()
    events.addBoilerplateToDescriptions('End time is approximate. See https://theottobar.com/calendar/ for more.')
    events.setColors('grape')

    return events

def blackCat():
    source = CalendarSource('https://www.blackcatdc.com/schedule.html', 'black_cat', options.remote)
    html = source.getHtml()

    parser = BlackCatParser(html, 'Black Cat')
    events = parser.parse().getEventsList()
    events.prefixDescriptionsWithLinks()
    events.addBoilerplateToDescriptions('End time is approximate. See https://www.blackcatdc.com/schedule.html for more.')
    events.setColors('flamingo')

    return events

def space2640():
    source = CalendarSource('https://www.2640space.net/events', '2640_space', options.remote)
    html = source.getHtml()

    parser = SquareSpaceParser(html, '2640 Space')
    events = parser.parse().getEventsList()
    events.prefixLinks('https://www.2640space.net')
    events.prefixDescriptionsWithLinks()
    events.addBoilerplateToDescriptions('See https://www.2640space.net/ for more.')
    events.setColors('blueberry')

    return events

def joeSquared():
    source = CalendarSource('https://www.joesquared.com/events/', 'joe_squared', options.remote)
    html = source.getHtml()

    parser = SquareSpaceParser(html, 'Joe Squared')
    events = parser.parse().getEventsList()
    events.prefixLinks('https://www.joesquared.com')
    events.prefixDescriptionsWithLinks()
    events.addBoilerplateToDescriptions('See https://www.joesquared.com/events/ for more.')
    events.setColors('tangerine')

    return events



if __name__ == '__main__':
    main()
