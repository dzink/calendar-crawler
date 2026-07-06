import os
import re
import html
import hashlib
from collections import OrderedDict
from datetime import datetime
from Assets import inlineCss, linkCss, inlineJs, linkJs

TEMPLATE_SRC = os.path.join(os.getcwd(), 'html-template')

with open(os.path.join(TEMPLATE_SRC, 'index.html')) as f:
    HTML_TEMPLATE = f.read()

with open(os.path.join(TEMPLATE_SRC, 'subscribe-dropdown.html')) as f:
    SUBSCRIBE_DROPDOWN_TEMPLATE = f.read().strip()

with open(os.path.join(TEMPLATE_SRC, 'faq.html')) as f:
    FAQ_TEMPLATE = f.read()

with open(os.path.join(TEMPLATE_SRC, 'footer.html')) as f:
    FOOTER_TEMPLATE = f.read().strip()


def buildDataAttrs(ev):
    """Return a string of data-* attributes for an event's <details> tag."""
    attrs = []
    if ev.id:
        hashed = hashlib.sha256(str(ev.id).encode()).hexdigest()[:16]
        attrs.append('data-id="%s"' % hashed)
    if ev.startDate:
        attrs.append('data-start="%s"' % ev.startDate.strftime('%Y-%m-%dT%H:%M:%S'))
    if ev.endDate:
        attrs.append('data-end="%s"' % ev.endDate.strftime('%Y-%m-%dT%H:%M:%S'))
    if ev.link or ev.urlTicket or ev.urlRsvp:
        attrs.append('data-link')
    if ev.img:
        attrs.append('data-flyer')
    if ev.isFree:
        attrs.append('data-free')
    if ev.isNotaflof:
        attrs.append('data-notaflof')
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
                parts[i] = _A_OPEN.sub('<a target="_blank" rel="noopener noreferrer" ', part)
        else:
            parts[i] = _BARE_URL.sub(r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', part)
    return ''.join(parts)


def buildHtml(events, source_list=None, base_url='', dev=False):
    """Build the full HTML string for the agenda page.

    Groups events by day into <section> elements, renders each event as a
    <details> with data-* attributes for the add-to-cal JS, and substitutes
    all {{placeholders}} in the HTML template including subscribe links
    derived from base_url.
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
            estimated = ev.timeIsEstimated
            location = html.escape(ev.location) if ev.location else ''
            link = html.escape(ev.link) if ev.link else ''
            url_ticket = html.escape(ev.urlTicket) if ev.urlTicket else ''
            url_rsvp = html.escape(ev.urlRsvp) if ev.urlRsvp else ''
            meta_parts = []
            if time_str:
                meta_parts.append(time_str + ('*' if estimated else ''))
            if location:
                meta_parts.append(location)
            free_tag = '<span class="sr-only">$free</span>' if ev.isFree else ''
            meta_line = '<span class="summary-meta">%s%s</span>' % (' &middot; '.join(meta_parts), free_tag) if meta_parts else ''
            summary_line = '<span class="summary-text"><span class="summary-title">%s</span>%s</span>' % (summary, meta_line)

            detail_lines = []
            if ev.startDate and ev.endDate:
                time_range = '%s – %s%s' % (ev.startDate.strftime('%-I:%M %p'), ev.endDate.strftime('%-I:%M %p'), '*' if estimated else '')
                detail_lines.append(
                    '<div class="time time-range"><time datetime="%s/%s">%s</time></div>' % (
                        ev.startDate.strftime('%Y-%m-%dT%H:%M'), ev.endDate.strftime('%Y-%m-%dT%H:%M'), html.escape(time_range)))
            elif ev.startDate:
                detail_lines.append(
                    '<div class="time"><time datetime="%s">%s</time></div>' % (
                        ev.startDate.strftime('%Y-%m-%dT%H:%M'), html.escape(ev.startDate.strftime('%-I:%M %p'))))
            if location:
                detail_lines.append('<div class="location">%s</div>' % location)
            else:
                detail_lines.append('<div class="location no-map">Check event for location</div>')
            if link:
                detail_lines.append(linkify('<div class="link-url"><a href="%s" title="%s">%s</a></div>' % (link, summary, link)))
            if url_ticket:
                detail_lines.append('<div class="link-url link-ticket"><a href="%s" target="_blank" rel="noopener noreferrer">Ticket link</a></div>' % url_ticket)
            if url_rsvp:
                detail_lines.append('<div class="link-url link-rsvp"><a href="%s" target="_blank" rel="noopener noreferrer">RSVP link</a></div>' % url_rsvp)
            flyer = ev.flyerHtml()
            if flyer:
                detail_lines.append(flyer)
            if ev.description:
                paragraphs = re.split(r'\n+', ev.description.strip())
                desc_html = ''.join('<p>%s</p>' % linkify(p) for p in paragraphs if p.strip())
                detail_lines.append('<div data-desc class="description">%s</div>' % desc_html)
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
            ics_url = base_url + '/assets/ics/%s.ics' % key
            source_links.append(
                '<li>%s <span>%d events</span>'
                ' <button class="subscribe-btn simple-link" data-ics-url="%s" data-name="%s" aria-expanded="false">subscribe</button></li>' % (
                    html.escape(name), count, html.escape(ics_url), html.escape(name)))
        source_ics_html = ''.join(source_links)

    # Build subscribe URLs from base_url for webcal, Google, Outlook, Office365
    base_url = base_url.rstrip('/')
    https_ics = base_url + '/assets/ics/events.ics'
    webcal_ics = https_ics.replace('https://', 'webcal://', 1)
    name = 'Baltimore DIY Calendar Crawler'
    encoded_name = html.escape(name, quote=True).replace(' ', '%20')

    footer = FOOTER_TEMPLATE.replace('{{faq_prefix}}', '')
    result = HTML_TEMPLATE.replace('{{content}}', ''.join(sections))
    result = result.replace('{{footer}}', footer)
    result = result.replace('{{subscribe_dropdown_template}}', SUBSCRIBE_DROPDOWN_TEMPLATE)
    result = result.replace('{{year}}', str(datetime.now().year))
    result = result.replace('{{source_ics_links}}', source_ics_html)
    result = result.replace('{{base_url}}', base_url)
    result = result.replace('{{webcal_ics}}', webcal_ics)
    result = result.replace('{{google_ics}}', 'https://calendar.google.com/calendar/r?cid=%s' % webcal_ics)
    result = result.replace('{{outlook_ics}}', 'https://outlook.live.com/calendar/0/addfromweb?url=%s&name=%s' % (https_ics, encoded_name))
    result = result.replace('{{office365_ics}}', 'https://outlook.office.com/calendar/0/addfromweb?url=%s&name=%s' % (https_ics, encoded_name))
    if dev:
        result = result.replace('{{styles}}', linkCss())
        result = result.replace('{{scripts}}', linkJs())
    else:
        result = result.replace('{{styles}}', inlineCss())
        result = result.replace('{{scripts}}', inlineJs())
    return result


def buildFaq(source_list=None, base_url='', dev=False):
    """Build the FAQ page HTML."""
    source_ics_html = ''
    if source_list:
        source_links = []
        for key, name, count in source_list:
            ics_url = base_url + '/assets/ics/%s.ics' % key
            source_links.append(
                '<li>%s <span>%d events</span></li>' % (
                    html.escape(name), count))
        source_ics_html = ''.join(source_links)

    base_url = base_url.rstrip('/')
    https_ics = base_url + '/assets/ics/events.ics'
    webcal_ics = https_ics.replace('https://', 'webcal://', 1)
    faq_name = 'Baltimore DIY Calendar Crawler'
    encoded_name = html.escape(faq_name, quote=True).replace(' ', '%20')

    footer = FOOTER_TEMPLATE.replace('{{faq_prefix}}', '../')
    result = FAQ_TEMPLATE
    result = result.replace('{{footer}}', footer)
    result = result.replace('{{year}}', str(datetime.now().year))
    result = result.replace('{{source_ics_links}}', source_ics_html)
    result = result.replace('{{base_url}}', base_url)
    result = result.replace('{{webcal_ics}}', webcal_ics)
    result = result.replace('{{google_ics}}', 'https://calendar.google.com/calendar/r?cid=%s' % webcal_ics)
    result = result.replace('{{outlook_ics}}', 'https://outlook.live.com/calendar/0/addfromweb?url=%s&name=%s' % (https_ics, encoded_name))
    result = result.replace('{{office365_ics}}', 'https://outlook.office.com/calendar/0/addfromweb?url=%s&name=%s' % (https_ics, encoded_name))
    if dev:
        result = result.replace('{{styles}}', '<link rel="stylesheet" href="../assets/css/minimal.css">')
        result = result.replace('{{scripts}}', '\n'.join('<script src="../assets/js/%s"></script>' % name.split('/')[-1] for name in ['js/theme.js']))
    else:
        result = result.replace('{{styles}}', inlineCss())
        result = result.replace('{{scripts}}', '<script>' + open(os.path.join(TEMPLATE_SRC, 'assets/js/theme.js')).read() + '</script>')
    return result
