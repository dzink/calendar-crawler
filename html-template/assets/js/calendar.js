/*
 * calendar.js — Add-to-calendar dropdown, ICS generation, webcal fallback.
 */

/* ===================== Add-to-Calendar dropdown ===================== */

/* One shared dropdown element is moved between events on click,
   keeping the DOM light for pages with 500+ events. */
var calDropdown = null;

/* Strip dashes/colons for Google/Yahoo/ICS date format (YYYYMMDDTHHmmss) */
function compactDate(iso) {
  return iso.replace(/[-:]/g, '');
}
/* Extract clean text from .details, skipping JS-injected elements */
var JS_INJECTED = '.row-icon, .map-toggle, .map-dropdown, .copy-url, .copy-event, .flyer-img, .desc-toggle';

function getDetailsText(details) {
  var detailsEl = details.querySelector('.details');
  if (!detailsEl) return '';
  var lines = [];
  for (var i = 0; i < detailsEl.children.length; i++) {
    var child = detailsEl.children[i];
    if (child.classList.contains('desc-toggle') || child.classList.contains('contextual-menu')) continue;
    if (child.classList.contains('flyer')) {
      var flyerBtn = child.querySelector('.flyer-toggle');
      if (flyerBtn) lines.push('Flyer: ' + flyerBtn.dataset.src);
      continue;
    }
    var clone = child.cloneNode(true);
    clone.querySelectorAll(JS_INJECTED).forEach(function(el) { el.remove(); });
    clone.querySelectorAll('a.url-stripped').forEach(function(a) { a.textContent = a.href; });
    if (clone.classList.contains('description')) {
      var pLines = [];
      var descContent = clone.querySelector('.row-content') || clone;
      for (var j = 0; j < descContent.children.length; j++) {
        var text = descContent.children[j].textContent.trim();
        if (text) pLines.push(text);
      }
      if (pLines.length) lines.push(pLines.join('\n\n'));
    } else {
      var text = clone.textContent.trim();
      if (text) lines.push(text);
    }
  }
  return lines.join('\n\n');
}

/* Read event data from the DOM and data-start/data-end attributes.
   Falls back to end-of-day if no end time is set. */
function getEventData(details) {
  var ds = details.dataset;
  var summaryText = details.querySelector('.summary-text');
  var titleEl = summaryText ? summaryText.childNodes[0] : null;
  var title = titleEl ? titleEl.textContent.trim() : 'Untitled';
  var locEl = details.querySelector('.location .row-content');
  if (!locEl) locEl = details.querySelector('.location');
  var location = locEl ? locEl.cloneNode(true) : null;
  if (location) {
    location.querySelectorAll('.row-icon, .map-toggle, .map-dropdown').forEach(function(el) { el.remove(); });
    location = location.textContent.trim();
  } else {
    location = '';
  }
  var linkEl = details.querySelector('.link-url a');
  var url = linkEl ? linkEl.href : '';
  var flyerEl = details.querySelector('.flyer-toggle');
  var img = flyerEl ? flyerEl.dataset.src : '';
  var desc = getDetailsText(details);
  if (desc) desc += '\n\nSee https:' + String.fromCharCode(47, 47) + 'shows.whomtube.com for more.';
  var d = { title: title, start: ds.start || '', location: location, url: url, img: img, desc: desc };
  if (ds.end) {
    d.end = ds.end;
  } else if (d.start) {
    d.end = d.start.replace(/T.*/, 'T23:59:59');
  } else {
    d.end = '';
  }
  return d;
}

/* --- Calendar URL builders --- */

function calGoogle(d) {
  var p = ['action=TEMPLATE', 'text=' + encodeURIComponent(d.title),
    'dates=' + compactDate(d.start) + '/' + compactDate(d.end),
    'ctz=America/New_York'];
  if (d.location) p.push('location=' + encodeURIComponent(d.location));
  if (d.desc) p.push('details=' + encodeURIComponent(d.desc));
  return _https + 'calendar.google.com/calendar/render?' + p.join('&');
}
function calOutlook(d) {
  var p = ['path=/calendar/action/compose', 'rru=addevent',
    'subject=' + encodeURIComponent(d.title),
    'startdt=' + encodeURIComponent(d.start),
    'enddt=' + encodeURIComponent(d.end)];
  if (d.location) p.push('location=' + encodeURIComponent(d.location));
  if (d.desc) p.push('body=' + encodeURIComponent(d.desc));
  return _https + 'outlook.live.com/calendar/0/action/compose?' + p.join('&');
}
function calYahoo(d) {
  var p = ['v=60', 'title=' + encodeURIComponent(d.title),
    'st=' + compactDate(d.start), 'et=' + compactDate(d.end)];
  if (d.location) p.push('in_loc=' + encodeURIComponent(d.location));
  if (d.desc) p.push('desc=' + encodeURIComponent(d.desc));
  return _https + 'calendar.yahoo.com/?' + p.join('&');
}
/* Build a minimal VCALENDAR string. Uses TZID=America/New_York since
   all crawled events are in the Baltimore area. */
function calIcs(d) {
  var lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-' + String.fromCharCode(47, 47) + 'CalendarCrawler' + String.fromCharCode(47, 47) + 'EN',
    'BEGIN:VEVENT',
    'DTSTART;TZID=America/New_York:' + compactDate(d.start),
    'DTEND;TZID=America/New_York:' + compactDate(d.end),
    'SUMMARY:' + d.title];
  if (d.location) lines.push('LOCATION:' + d.location);
  if (d.url) lines.push('URL:' + d.url);
  if (d.desc) lines.push('DESCRIPTION:' + d.desc);
  if (d.img) lines.push('ATTACH;FMTTYPE=image/jpeg:' + d.img);
  lines.push('END:VEVENT', 'END:VCALENDAR');
  return lines.join('\r\n');
}

/* --- Dropdown DOM and event handling --- */

/* Create the dropdown once, reuse it for every event */
function ensureDropdown() {
  if (calDropdown) return calDropdown;
  calDropdown = document.createElement('div');
  calDropdown.className = 'cal-dropdown';
  calDropdown.setAttribute('role', 'menu');
  calDropdown.setAttribute('aria-label', 'Add to your calendars options');
  calDropdown.innerHTML = '<span class="cal-note">Single event only. Will not auto-update — check back for changes.</span>'
    + '<a href="#" data-cal="ics" role="menuitem" class="cal-primary">Download .ics</a> / '
    + '<a href="#" data-cal="google" role="menuitem">Google Calendar</a> / '
    + '<a href="#" data-cal="outlook" role="menuitem">Outlook</a> / '
    + '<a href="#" data-cal="yahoo" role="menuitem">Yahoo Calendar</a>';
  return calDropdown;
}
function closeCal() {
  if (calDropdown) {
    calDropdown.classList.remove('open');
    var prev = calDropdown.previousElementSibling;
    if (prev) prev.setAttribute('aria-expanded', 'false');
  }
}
/* Click delegation: .add-to-cal toggles the dropdown, .cal-dropdown a
   fires the appropriate calendar action, anything else closes it. */
document.addEventListener('click', function(e) {
  var trigger = e.target.closest('.add-to-cal');
  if (trigger) {
    var dd = ensureDropdown();
    var isOpen = dd.classList.contains('open') && trigger.nextElementSibling === dd;
    closeCal();
    if (isOpen) return;
    trigger.after(dd);
    dd.classList.add('open');
    trigger.setAttribute('aria-expanded', 'true');
    scrollIntoViewSmooth(dd);
    return;
  }
  var calLink = e.target.closest('.cal-dropdown a');
  if (calLink) {
    e.preventDefault();
    var details = calLink.closest('details');
    var d = getEventData(details);
    var type = calLink.dataset.cal;
    if (type === 'google') window.open(calGoogle(d), '_blank');
    else if (type === 'outlook') window.open(calOutlook(d), '_blank');
    else if (type === 'yahoo') window.open(calYahoo(d), '_blank');
    else if (type === 'ics') {
      var blob = new Blob([calIcs(d)], { type: 'text/calendar' });
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = (d.title.replace(/[^a-z0-9]+/gi, '-').substring(0, 40)) + '.ics';
      a.click();
      URL.revokeObjectURL(a.href);
    }
    closeCal();
    return;
  }
  if (calDropdown && !e.target.closest('.cal-dropdown')) closeCal();
});

/* ===================== Webcal fallback ===================== */

/* If the webcal link doesn't open an app, show the alt text */
document.addEventListener('click', function(e) {
  var link = e.target.closest('a[href^="webcal:"]');
  if (!link) return;
  var alt = document.querySelector('.subheader-alt');
  if (!alt) return;
  var hidden = !document.hidden;
  function onHide() { hidden = false; }
  document.addEventListener('visibilitychange', onHide);
  setTimeout(function() {
    document.removeEventListener('visibilitychange', onHide);
    if (hidden) alt.classList.add('webcal-fallback');
  }, 1500);
});
