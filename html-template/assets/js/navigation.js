/*
 * navigation.js — Scroll navigation, date picker, focus management.
 *
 * Note: This file is minified at build time by a naive regex minifier in
 * calendar-export.py. Avoid // inside string literals — use
 * String.fromCharCode(47, 47) or the _https helper instead.
 */

/* ===================== Shared globals ===================== */

var agenda = document.getElementById('agenda');
var nav = document.querySelector('nav.date-picker');
var _https = 'https:' + String.fromCharCode(47, 47);

function scrollIntoViewSmooth(el, block) {
  requestAnimationFrame(function() {
    el.scrollIntoView({ behavior: 'smooth', block: block || 'nearest' });
  });
}

/* ===================== Navigation helpers ===================== */

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
    var focused = document.activeElement;
    if (focused && focused !== agenda) {
      var rect = focused.getBoundingClientRect();
      var nh = navHeight();
      if (rect.top < nh) {
        window.scrollBy(0, rect.top - nh - 10);
      }
    }
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
      var det = document.activeElement.closest('details');
      if (det && det.open) {
        det.open = false;
        det.querySelector('summary').focus();
        return;
      }
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
  if (exact && exact.style.display !== 'none') { scrollToSection(exact); return; }
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
