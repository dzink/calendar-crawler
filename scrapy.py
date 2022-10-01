import sys
sys.path.append('./src')

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

def main():
    gcb = GoogleCalendarBuilder()
    events = showPlace()
    print(events.events[0])
    # event = events.events[0]
    # event.setSummary('New Summaryyy')

    # events.deduplicate()
    # calendarId = gcb.getCalendarIdFromFile('data/testcalendarid.txt')
    # gcb.syncList(events, calendarId)
    # events.write()


    # calendarEventId = gcb.syncEvent(event, calendarId)
    # print(['ceid', calendarEventId])
    # event.setCalendarId(calendarEventId)
    # event.write()

def redEmmas():
    source = CalendarSource('https://withfriends.co/red_emmas/events', 'red_emmas')
    # html = source.getRemoteHtml()
    html = source.getLocalHtml()

    parser = WithFriendsParser(html, 'Red Emma\'s')
    events = parser.parse().getEventsList()

    events.addBoilerplateToDescriptions('End time is approximate. Imported from https://withfriends.co/red_emmas/events')
    events.prefixLinks('https://withfriends.co')
    events.prefixDescriptionsWithLinks()
    events.setAbsoluteEndDateTime(22, 00)
    events.setLocationAddress('Red Emma\'s')

    return events

def currentSpace():
    source = CalendarSource('https://withfriends.co/current_space/events', 'current_space')
    # html = source.getRemoteHtml()
    html = source.getLocalHtml()

    parser = WithFriendsParser(html)
    events = parser.parse().getEventsList()

    events.addBoilerplateToDescriptions('End time is approximate, events end by 10:30. Imported from https://withfriends.co/current_space/events')
    events.prefixLinks('https://withfriends.co')
    events.prefixDescriptionsWithLinks()
    events.setAbsoluteEndDateTime(22, 30)
    events.setLocationAddress('Current Space')

    return events

def showPlace():
    showplaceSource = CalendarSource('https://baltshowplace.tumblr.com/', 'showplace')
    # html = showplaceSource.getRemoteHtml()
    html = showplaceSource.getLocalHtml()

    parser = ShowPlaceParser(html, 'ShowPlace')
    events = parser.parse().getEventsList()

    # Reject events that come from other sources
    events.rejectEvents({'location': '(Ottobar|Red Emma\'s|Current Space)'})

    events.addBoilerplateToDescriptions('End times are approximate. Thanks to the ShowPlace folks for this event. See https://baltshowplace.tumblr.com/ for more')
    events.setAbsoluteEndDateTime(23, 59)

    return events

def ottobar():
    source = CalendarSource('https://theottobar.com/calendar/', 'ottobar')
    # html = source.getRemoteHtml()
    html = source.getLocalHtml()

    parser = OttobarParser(html, 'Ottobar')
    events = parser.parse().getEventsList()
    events.prefixDescriptionsWithLinks()
    events.addBoilerplateToDescriptions('End time is approximate. Imported from https://theottobar.com/calendar/')

    return events



if __name__ == '__main__':
    main()
