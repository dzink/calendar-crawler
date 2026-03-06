from WithFriendsParser import WithFriendsParser
from Event import Event
from CalendarLogger import logger
import re

class CurrentSpaceParser(WithFriendsParser):
    """
    WithFriends updated their layout for some venues to use ticketContainer/ticketCard
    instead of the old wf-event list items. This subclass handles the new format.
    """

    def parseEvents(self, html, settings = {}):
        soup = self.soup(html)
        container = soup.find(class_='ticketContainer')

        if not container:
            logger.warning('No ticketContainer found, falling back to old WithFriends parser')
            return super().parseEvents(html, settings)

        for card in container.find_all('div', class_='ticketCard'):
            try:
                event = Event()

                link_el = card.find('a')
                if not link_el or not link_el.get('href'):
                    continue
                href = link_el.get('href')
                if not href.startswith('http'):
                    href = 'https://withfriends.co' + href
                event.setLink(href)

                title_el = card.find(class_='eventTitleMobile')
                if not title_el:
                    continue
                event.setSummary(title_el.get_text().strip())

                date_el = card.find(class_='imageTextUpperLeft')
                if date_el:
                    date_text = date_el.get_text().strip()
                    # Format: "Wed, Mar 4 at 6:00 PM"
                    # Strip the short day name prefix since it can mismatch across years
                    date_text = re.sub(r'^[A-Z][a-z]{2},\s*', '', date_text)
                    # Now: "Mar 4 at 6:00 PM"
                    fmt = '%b %d at %I:%M %p'
                    year = event.getNearestYear(date_text, fmt)
                    event.setStartString(date_text + str(year), fmt + '%Y')

                img = card.find('img')
                if img:
                    event.setImg(img.get('data-image') or img.get('src'), img.get('alt'))

                self.removeScriptsFromElement(card)
                description = self.getDescriptionText(card)
                description = self.replaceWhitespaceWithPipes(description)
                event.setDescription(description)

                self.addEvent(event)
            except Exception as e:
                eventText = self.replaceWhitespaceWithPipes(card.get_text())
                logger.exception("Exception occurred in " + eventText)

        return self
