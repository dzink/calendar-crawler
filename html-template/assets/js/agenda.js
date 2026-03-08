/*
 * agenda.js — UI logic for the HTML agenda page.
 *
 * Sections:
 *   Navigation    — scroll-to-section, date picker sync, day/week/month nav
 *   Focus mgmt    — keyboard focus tracking, Escape to nav, toolbar arrows
 *   Filtering     — comma-separated text filter across all events
 *   View/theme    — day/week toggle, stage-mode toggle (persisted in localStorage)
 *   Flyer         — click-to-load event flyer images
 *   Map links     — per-event map provider links (OSM, DDG, Google, geo:)
 *   Add-to-cal    — per-event dropdown generating Google/Outlook/Yahoo URLs
 *                      and .ics blob downloads. Uses a single shared dropdown
 *                      element moved between events to keep the DOM light.
 *
 * Event data for add-to-cal comes from data-* attributes on each <details>
 * element (data-title, data-start, data-end, data-location, data-url) and the
 * description paragraph marked with data-desc.
 *
 * Note: This file is minified at build time by a naive regex minifier in
 * calendar-export.py. Avoid // inside string literals — use
 * String.fromCharCode(47, 47) or the _https helper instead.
 */
/* ===================== Navigation helpers ===================== */

var agenda = document.getElementById('agenda');
var nav = document.querySelector('nav.date-picker');

/* Each day is a <section id="day-YYYY-MM-DD"> in the agenda grid */
function getSections(includeHidden) {
  var all = Array.from(agenda.querySelectorAll('section[id^="day-"]'));
  if (includeHidden) return all;
  return all.filter(function(s) { return s.style.display !== 'none'; });
}
function navHeight() {
  return nav ? nav.offsetHeight : 0;
}
/* Absolute Y position of a section, accounting for sticky nav */
function posOf(sec) {
  return sec.getBoundingClientRect().top + window.scrollY - navHeight();
}
/* Parse a section's id into a Date */
function dateOf(sec) {
  return new Date(sec.id.replace('day-', '') + 'T00:00:00');
}
/* Week mode = wide viewport + not explicitly toggled to day view */
function isWeekMode() {
  return window.innerWidth >= 1024 && !document.body.classList.contains('day-view');
}
/* Find the index of the section currently at the top of the viewport */
function currentIndex() {
  var sections = getSections();
  if (isWeekMode()) {
    for (var i = 0; i < sections.length; i++) {
      if (sections[i].style.display !== 'none') return i;
    }
    return 0;
  }
  var top = window.scrollY + navHeight() + 10;
  var idx = 0;
  for (var i = 0; i < sections.length; i++) {
    var secTop = sections[i].getBoundingClientRect().top + window.scrollY;
    if (secTop <= top) idx = i;
  }
  return idx;
}
/* pendingIndex tracks where we're scrolling TO, so rapid nav presses
   step from the destination rather than the current scroll position */
var pendingIndex = -1;
var lastFocusedIndex = -1;
function scrollToSection(sec) {
  var sections = getSections();
  for (var i = 0; i < sections.length; i++) {
    if (sections[i] === sec) { pendingIndex = i; break; }
  }
  if (isWeekMode()) {
    sec.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  } else {
    window.scrollTo({ top: posOf(sec), behavior: 'smooth' });
  }
}
/* ===================== Focus management ===================== */

/* savedFocus/savedDate let Escape→Tab restore focus to the last event */
var savedFocus = null;
var savedDate = null;
/* focusin bubbles (unlike focus), so we can track focus across the whole agenda */
var _redirectingFocus = false;
var _shiftTabbing = false;
var _mouseInDetails = false;
agenda.addEventListener('mousedown', function(e) {
  _mouseInDetails = !!e.target.closest('.details');
});
agenda.addEventListener('mouseup', function() {
  _mouseInDetails = false;
});
document.addEventListener('keydown', function(e) {
  _shiftTabbing = e.key === 'Tab' && e.shiftKey;
});
document.addEventListener('focusin', function(e) {
  if (!agenda.contains(e.target)) return;
  // Track which section last had focus
  var sections = getSections();
  for (var i = 0; i < sections.length; i++) {
    if (sections[i].contains(e.target)) { lastFocusedIndex = i; break; }
  }
  // If the agenda container itself got focus, redirect to a summary
  // (but let Shift-Tab pass through so the user can leave the agenda,
  // and skip if a click landed inside .details so text selection works)
  if (e.target === agenda) {
    if (_shiftTabbing) return;
    if (_mouseInDetails) return;
    _redirectingFocus = true;
    if (savedFocus && savedDate === picker.value && agenda.contains(savedFocus)) {
      savedFocus.focus({ preventScroll: true });
    } else {
      var idx = lastFocusedIndex >= 0 && lastFocusedIndex < sections.length ? lastFocusedIndex : currentIndex();
      var target = sections[idx];
      if (target) {
        var el = target.querySelector('summary');
        if (el) el.focus({ preventScroll: true });
      }
    }
    _redirectingFocus = false;
    savedFocus = null;
    savedDate = null;
    return;
  }
  // If a focused element lands behind the sticky nav, nudge it into view
  // (skip when focus was programmatically redirected with preventScroll)
  if (!_redirectingFocus) {
    var rect = e.target.getBoundingClientRect();
    var nh = navHeight();
    var target = nh + window.innerHeight * 0.4;
    if (rect.top < nh) {
      window.scrollBy(0, rect.top - target);
    }
  }
});
/* Escape: close cal dropdown first, then fall through to move focus to nav */
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    if (calDropdown && calDropdown.classList.contains('open')) {
      e.preventDefault();
      closeCal();
      return;
    }
    if (agenda.contains(document.activeElement)) {
      e.preventDefault();
      savedFocus = document.activeElement;
      savedDate = picker.value;
      var btns = nav.querySelectorAll('.btnset button');
      for (var i = 0; i < btns.length; i++) {
        if (btns[i].offsetParent !== null) { btns[i].focus(); return; }
      }
      picker.focus();
    }
  }
});
/* ===================== Date picker sync ===================== */

var picker = document.getElementById('datepicker');
/* Debounced scroll handler keeps the date input in sync with the visible day */
var scrollTimer;
window.addEventListener('scroll', function() {
  clearTimeout(scrollTimer);
  scrollTimer = setTimeout(function() {
    var sections = getSections();
    var cur = currentIndex();
    if (cur >= 0) picker.value = sections[cur].id.replace('day-', '');
    pendingIndex = -1;
  }, 150);
});
/* Set initial datepicker value to the first day section */
(function() {
  var sections = getSections();
  if (sections.length) picker.value = sections[0].id.replace('day-', '');
})();
/* Jump to a specific date; if no exact match, find the nearest later day */
function goToDate(val) {
  savedFocus = null; savedDate = null; lastFocusedIndex = -1;
  if (!val) return;
  var exact = document.getElementById('day-' + val);
  if (exact) { scrollToSection(exact); return; }
  var sections = getSections();
  for (var i = 0; i < sections.length; i++) {
    if (sections[i].id.replace('day-', '') >= val) { scrollToSection(sections[i]); return; }
  }
  if (sections.length) scrollToSection(sections[sections.length - 1]);
}
/* Navigate by day, week, or month. dir is +1 (forward) or -1 (back). */
function go(dir, mode) {
  savedFocus = null; savedDate = null; lastFocusedIndex = -1;
  var sections = getSections();
  var cur = pendingIndex >= 0 ? pendingIndex : currentIndex();
  if (!sections.length) return;
  var refDate = dateOf(sections[cur]);

  if (mode === 'day') {
    var t = cur + dir;
    if (t >= 0 && t < sections.length) { scrollToSection(sections[t]); return; }
    if (t < 0) { window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
    return;
  }

  if (mode === 'week') {
    var target = refDate.getTime() + dir * 7 * 86400000;
    var best = -1, bestDiff = Infinity;
    for (var i = 0; i < sections.length; i++) {
      if (dir === 1 ? i <= cur : i >= cur) continue;
      var diff = Math.abs(dateOf(sections[i]).getTime() - target);
      if (diff < bestDiff) { bestDiff = diff; best = i; }
    }
    if (best >= 0) { scrollToSection(sections[best]); return; }
    if (dir === -1) { window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
    scrollToSection(sections[sections.length - 1]);
    return;
  }

  if (mode === 'month') {
    var refM = refDate.getFullYear() * 12 + refDate.getMonth();
    if (dir === 1) {
      for (var i = cur + 1; i < sections.length; i++) {
        if (dateOf(sections[i]).getFullYear() * 12 + dateOf(sections[i]).getMonth() > refM) {
          scrollToSection(sections[i]); return;
        }
      }
      scrollToSection(sections[sections.length - 1]);
    } else {
      var prevM = -1;
      for (var i = cur - 1; i >= 0; i--) {
        var m = dateOf(sections[i]).getFullYear() * 12 + dateOf(sections[i]).getMonth();
        if (m < refM) { prevM = m; break; }
      }
      if (prevM >= 0) {
        for (var i = 0; i < sections.length; i++) {
          if (dateOf(sections[i]).getFullYear() * 12 + dateOf(sections[i]).getMonth() === prevM) {
            scrollToSection(sections[i]); return;
          }
        }
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }
}
/* Arrow-key navigation within toolbar buttons (WAI-ARIA toolbar pattern) */
document.querySelectorAll('[role="toolbar"]').forEach(function(toolbar) {
  var items = Array.from(toolbar.querySelectorAll('a, button:not(#theme-toggle)'));
  toolbar.addEventListener('keydown', function(e) {
    var active = document.activeElement;
    var idx = items.indexOf(active);
    if (idx < 0) return;
    var next = -1;
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = (idx + 1) % items.length;
    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = (idx - 1 + items.length) % items.length;
    if (e.key === 'Home') next = 0;
    if (e.key === 'End') next = items.length - 1;
    if (next < 0) return;
    e.preventDefault();
    items[idx].setAttribute('tabindex', '-1');
    items[next].setAttribute('tabindex', '0');
    items[next].focus();
  });
});
/* ===================== Event filtering ===================== */

/* Comma-separated filter: all terms must match an event's text content */
var filterClear = document.getElementById('filter-clear');
var filterInput = document.getElementById('event-filter');
function clearFilter() {
  filterInput.value = '';
  filterEvents('');
  filterInput.focus();
}
function filterEvents(query) {
  filterClear.hidden = !query;
  var terms = query.toLowerCase().split(',').map(function(t) { return t.trim(); }).filter(Boolean);
  var sections = getSections(true);
  for (var i = 0; i < sections.length; i++) {
    var sec = sections[i];
    var events = sec.querySelectorAll('details');
    var anyVisible = false;
    for (var j = 0; j < events.length; j++) {
      var text = events[j].textContent.toLowerCase();
      var match = true;
      for (var k = 0; k < terms.length; k++) {
        if (text.indexOf(terms[k]) < 0) { match = false; break; }
      }
      events[j].style.display = match ? '' : 'none';
      if (match) anyVisible = true;
    }
    sec.style.display = anyVisible || !terms.length ? '' : 'none';
  }
}
filterInput.addEventListener('keydown', function(e) {
  if (e.key === 'Enter') {
    e.preventDefault();
    var match = agenda.querySelector('details:not([style*="none"]) summary');
    if (match) match.focus();
  }
});
/* Scroll an element into view on the next frame */
function scrollIntoViewSmooth(el, block) {
  requestAnimationFrame(function() {
    el.scrollIntoView({ behavior: 'smooth', block: block || 'nearest' });
  });
}

/* Auto-scroll to an event when it's opened, inject date and row-icon labels */
var ROW_ICON_LABELS = {
  time: 'Time', location: 'Location', 'link-url': 'Link',
  description: 'Description', flyer: 'Flyer'
};
function injectRowIcons(det) {
  var details = det.querySelector('.details');
  if (!details) return;
  for (var i = 0; i < details.children.length; i++) {
    var child = details.children[i];
    if (child.querySelector('.row-icon')) continue;
    var label = null;
    for (var cls in ROW_ICON_LABELS) {
      if (child.classList.contains(cls)) { label = ROW_ICON_LABELS[cls]; break; }
    }
    if (!label) continue;
    var icon = document.createElement('span');
    icon.className = 'row-icon';
    icon.title = label;
    var hidden = document.createElement('span');
    hidden.className = 'hidden';
    hidden.textContent = label + ':';
    icon.appendChild(hidden);
    var content = document.createElement('span');
    content.className = 'row-content';
    while (child.firstChild) content.appendChild(child.firstChild);
    child.appendChild(icon);
    child.appendChild(content);
  }
}
agenda.addEventListener('toggle', function(e) {
  var det = e.target;
  if (det.tagName === 'DETAILS' && det.open) {
    injectRowIcons(det);
    var timeEl = det.querySelector('.time .row-content');
    if (timeEl && !timeEl.querySelector('.date-label')) {
      var sec = det.closest('section');
      if (sec) {
        var dateStr = sec.id.replace('day-', '');
        var parts = dateStr.split('-');
        var span = document.createElement('span');
        span.className = 'date-label';
        span.textContent = ', ' + parts[1] + '-' + parts[2] + '-' + parts[0];
        timeEl.append(span);
      }
    }
    scrollIntoViewSmooth(det);
  }
}, true);
/* Handle anchor links to sections/details (e.g. sidebar "About" links) */
document.addEventListener('click', function(e) {
  var link = e.target.closest('a[href^="#"]');
  if (!link) return;
  var id = link.getAttribute('href').slice(1);
  var target = document.getElementById(id);
  if (!target) return;
  e.preventDefault();
  if (target.tagName === 'DETAILS') target.open = true;
  target.scrollIntoView({ behavior: 'instant' });
});
/* ===================== View and theme toggles ===================== */

/* Stage mode: high-contrast red-on-black theme for dark venues */
var THEME_DARK_CLASS = 'dark';
var THEME_LIGHT_CLASS = 'light';

function updateThemeToggle(on) {
  var btn = document.getElementById('theme-toggle');
  btn.className = on ? THEME_LIGHT_CLASS : THEME_DARK_CLASS;
  btn.querySelector('.hidden').textContent = on ? 'Switch to dark theme' : 'Switch to light theme';
}

function toggleTheme() {
  document.body.classList.toggle('stage-theme');
  var on = document.body.classList.contains('stage-theme');
  localStorage.setItem('stage-theme', on ? '1' : '');
  updateThemeToggle(on);
}
(function() {
  if (localStorage.getItem('stage-theme') === '1') {
    document.body.classList.add('stage-theme');
    updateThemeToggle(true);
  }
})();
/* Webcal fallback: if the link doesn't open an app, show the alt text */
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
/* ===================== Flyer image loader ========================== */
agenda.addEventListener('click', function(e) {
  var flyer = e.target.closest('.details > .flyer');
  if (!flyer) return;
  var link = e.target.closest('a');
  if (!link) return;
  e.preventDefault();
  if (link.classList.contains('flyer-hide')) {
    flyer.querySelector('.flyer-img').remove();
    flyer.querySelector('.flyer-hide').remove();
    flyer.querySelector('a').style.display = '';
  } else {
    var img = document.createElement('img');
    img.src = link.href;
    img.alt = link.dataset.alt || '';
    img.className = 'flyer-img';
    link.style.display = 'none';
    var hide = document.createElement('a');
    hide.href = '#';
    hide.className = 'flyer-hide';
    hide.textContent = 'Hide Flyer';
    flyer.appendChild(hide);
    flyer.appendChild(img);
    img.onload = function() { scrollIntoViewSmooth(flyer); };
  }
});
/* ===================== Map links ====================================== */
/* _https avoids a literal // in a string, which the naive minifier
   would strip as a line comment. See EXPORT.md. */
var _https = 'https:' + String.fromCharCode(47, 47);
var mapDropdown = null;

function ensureMapDropdown() {
  if (mapDropdown) return mapDropdown;
  mapDropdown = document.createElement('span');
  mapDropdown.className = 'map-dropdown';
  return mapDropdown;
}

function closeMap() {
  if (mapDropdown) mapDropdown.classList.remove('open');
}

function buildMapLinks(location) {
  var q = encodeURIComponent(location + ' maryland');
  var ddg = _https + 'duckduckgo.com/?q=' + q + '&iaxm=maps';
  var gm = _https + 'www.google.com/maps/search/' + q;
  return 'some guesses:'
    + '<a href="' + ddg + '" target="_blank">DuckDuckGo</a> / '
    + '<a href="' + gm + '" target="_blank">Google</a>';
}

agenda.addEventListener('click', function(e) {
  var trigger = e.target.closest('.map-toggle');
  if (trigger) {
    e.preventDefault();
    var dd = ensureMapDropdown();
    var isOpen = dd.classList.contains('open') && trigger.nextElementSibling === dd;
    closeMap();
    if (isOpen) return;
    var loc = trigger.closest('.details').querySelector('.location');
    if (!loc) return;
    var clone = loc.cloneNode(true);
    clone.querySelectorAll('.map-toggle, .map-dropdown').forEach(function(el) { el.remove() });
    dd.innerHTML = buildMapLinks(clone.textContent);
    trigger.after(dd);
    dd.classList.add('open');
    return;
  }
  if (mapDropdown && !e.target.closest('.map-dropdown') && !e.target.closest('.map-toggle')) closeMap();
});

/* Inject [map] toggle after each location element */
agenda.querySelectorAll('.location').forEach(function(loc) {
  var btn = document.createElement('a');
  btn.href = '#';
  btn.className = 'map-toggle';
  btn.textContent = '[map options]';
  loc.append(btn);
});

/* ===================== Copy URL button =============================== */
agenda.querySelectorAll('.link-url a').forEach(function(link) {
  var btn = document.createElement('button');
  btn.className = 'copy-url';
  btn.title = 'Copy URL';
  btn.setAttribute('aria-label', 'Copy URL');
  link.after(btn);
});

/* ===================== Copy buttons (delegated) ====================== */
function flashCopied(btn) {
  btn.classList.add('copied');
  setTimeout(function() { btn.classList.remove('copied'); }, 1500);
}
agenda.addEventListener('click', function(e) {
  var btn = e.target.closest('.copy-url');
  if (btn) {
    e.preventDefault();
    var link = btn.previousElementSibling;
    if (link) navigator.clipboard.writeText(link.href);
    flashCopied(btn);
    return;
  }
  btn = e.target.closest('.copy-event');
  if (btn) {
    e.preventDefault();
    var details = btn.closest('details');
    var d = getEventData(details);
    var date = details.closest('section').querySelector('h2').textContent.trim();
    navigator.clipboard.writeText(d.title + '\n\n' + date + '\n\n' + d.desc);
    flashCopied(btn);
    return;
  }
});

/* ===================== Contextual menu (injected on open) ============ */
agenda.addEventListener('toggle', function(e) {
  var det = e.target;
  if (!det.open || det.querySelector('.contextual-menu')) return;
  var sec = document.createElement('section');
  sec.className = 'contextual-menu';
  sec.setAttribute('aria-label', 'Event actions');
  // var copyBtn = document.createElement('button');
  // copyBtn.className = 'copy-event';
  // copyBtn.setAttribute('aria-label', 'Copy event details');
  // copyBtn.title = 'Copy event details';
  sec.innerHTML = '<button class="copy-event btn tertiary-btn" aria-label="Copy event details" title="Copy event details"><span class="hidden">Copy Details</span></button>'
    + '<button class="add-to-cal btn secondary-btn" aria-haspopup="menu" aria-expanded="false">add to calendar</button>';
  det.appendChild(sec);
}, true);

/* ===================== Add-to-Calendar dropdown ===================== */

/* One shared dropdown element is moved between events on click,
   keeping the DOM light for pages with 500+ events. */
var calDropdown = null;

/* Strip dashes/colons for Google/Yahoo/ICS date format (YYYYMMDDTHHmmss) */
function compactDate(iso) {
  return iso.replace(/[-:]/g, '');
}
/* Extract clean text from .details, skipping JS-injected elements */
var JS_INJECTED = '.row-icon, .map-toggle, .map-dropdown, .copy-url, .copy-event, .flyer-img, .flyer-hide';

function getDetailsText(details) {
  var detailsEl = details.querySelector('.details');
  if (!detailsEl) return '';
  var lines = [];
  for (var i = 0; i < detailsEl.children.length; i++) {
    var child = detailsEl.children[i];
    if (child.classList.contains('flyer')) {
      var flyerLink = child.querySelector('a');
      if (flyerLink) lines.push('Flyer: ' + flyerLink.href);
      continue;
    }
    var clone = child.cloneNode(true);
    clone.querySelectorAll(JS_INJECTED).forEach(function(el) { el.remove(); });
    if (clone.classList.contains('description')) {
      var pLines = [];
      for (var j = 0; j < clone.children.length; j++) {
        var text = clone.children[j].textContent.trim();
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
  var locEl = details.querySelector('.location');
  var location = locEl ? locEl.childNodes[0].textContent.trim() : '';
  var linkEl = details.querySelector('.link-url a');
  var url = linkEl ? linkEl.href : '';
  var flyerEl = details.querySelector('.flyer a');
  var img = flyerEl ? flyerEl.href : '';
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
