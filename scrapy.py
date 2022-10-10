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
from ShowPlaceParser import ShowPlaceParser
from OttobarParser import OttobarParser
from WithFriendsParser import WithFriendsParser

from time import sleep

remote = None
forceUpdateIfMatched = None
dryRun = None

def main():
    parseArguments()
    print(forceUpdateIfMatched)
    gcb = GoogleCalendarBuilder()
    calendarId = gcb.getCalendarIdFromFile('data/testcalendarid.txt')

    events = []

    events = events + showPlace().events
    events = events + ottobar().events
    events = events + redEmmas().events
    events = events + currentSpace().events

    for event in events:
        event.deduplicate(forceUpdateIfMatched = forceUpdateIfMatched)
        if (not dryRun):
            gcb.syncEvent(event, calendarId)
            event.write()
        else:
            gcb.dryRun(event)

def parseArguments():
    global remote
    global dryRun
    global forceUpdateIfMatched
    parser = argparse.ArgumentParser(description='Scrape event pages and add them to a Google calendar')
    parser.add_argument('-l', '--local', help = 'Whether to use local cached sources instead of re-scraping html.', action = 'store_false', default = True)
    parser.add_argument('-u', '--force-update', help = 'Whether to force Google Calendar updates, even if there\'s nothing to update.', action = 'store_true', default = False)
    parser.add_argument('-d', '--dry-run', help = 'Run the parser but do not write to the calendar or database.', action = 'store_true', default = False)
    args = parser.parse_args()
    print(args)
    remote = args.local
    forceUpdateIfMatched = args.force_update
    dryRun = args.dry_run

def redEmmas():
    source = CalendarSource('https://withfriends.co/red_emmas/events', 'red_emmas', remote)
    source.setScrollCount(4)
    html = source.getHtml()

    parser = WithFriendsParser(html, 'Red Emma\'s')
    events = parser.parse().getEventsList()

    events.addBoilerplateToDescriptions('End time is approximate. See https://withfriends.co/red_emmas/events for more.')
    events.prefixDescriptionsWithLinks()
    events.setAbsoluteEndDateTime(22, 00)
    events.setLocationAddress('Red Emma\'s')

    return events

def currentSpace():
    source = CalendarSource('https://withfriends.co/current_space/events', 'current_space', remote)
    source.setScrollCount(4)
    html = source.getHtml()

    parser = WithFriendsParser(html, 'Current Space')
    events = parser.parse().getEventsList()

    events.addBoilerplateToDescriptions('End time is approximate. See https://withfriends.co/current_space/events for more.')
    events.prefixDescriptionsWithLinks()
    events.setAbsoluteEndDateTime(22, 30)
    events.setLocationAddress('Current Space')

    return events

def showPlace():
    showplaceSource = CalendarSource('https://baltshowplace.tumblr.com/', 'showplace', remote)
    html = showplaceSource.getHtml()

    parser = ShowPlaceParser(html, 'ShowPlace')
    parser.setPostOffset(0)
    events = parser.parse().getEventsList()

    # Reject events that come from other scraped sources
    events.rejectEvents({'location': '(Ottobar|Red Emma\'s|Current Space)'})

    events.addBoilerplateToDescriptions('End times are approximate. See https://baltshowplace.tumblr.com/ for more.')

    return events

def ottobar():
    source = CalendarSource('https://theottobar.com/calendar/', 'ottobar', remote)
    html = source.getHtml()

    parser = OttobarParser(html, 'Ottobar')
    events = parser.parse().getEventsList()
    events.prefixDescriptionsWithLinks()
    events.addBoilerplateToDescriptions('End time is approximate. See https://theottobar.com/calendar/ for more.')

    return events



if __name__ == '__main__':
    main()
