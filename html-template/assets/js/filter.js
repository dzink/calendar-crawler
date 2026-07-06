/*
 * filter.js — Keyword and location filtering.
 */

/* ===================== Event filtering ===================== */

/* Comma-separated filter: all terms must match an event's text content */
var filterClear = document.getElementById('filter-clear');
var filterInput = document.getElementById('event-filter');
var activeLocationFilter = '';
function clearFilter() {
  filterInput.value = '';
  activeLocationFilter = '';
  filterEvents('');
  filterInput.focus();
}
function filterEvents(query) {
  filterClear.hidden = !query && !activeLocationFilter;
  var terms = query.toLowerCase().split(',').map(function(t) { return t.trim(); }).filter(Boolean);
  if (activeLocationFilter) terms.push(activeLocationFilter.toLowerCase());
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
  if (terms.length) {
    var first = getSections()[0];
    if (first) scrollToSection(first);
  }
}
filterInput.addEventListener('keydown', function(e) {
  if (e.key === 'Escape' && filterInput.value) {
    e.preventDefault();
    e.stopPropagation();
    filterInput.value = '';
    filterEvents('');
    return;
  }
  if (e.key === 'Enter') {
    e.preventDefault();
    var match = agenda.querySelector('details:not([style*="none"]) summary');
    if (match) match.focus();
  }
});

/* ===================== Location filter ===================== */

var locationBtn = document.getElementById('location-filter');
var locationDropdown = null;

function getLocationCounts() {
  var counts = {};
  var events = agenda.querySelectorAll('details');
  for (var i = 0; i < events.length; i++) {
    if (events[i].style.display === 'none') continue;
    var sec = events[i].closest('section');
    if (sec && sec.style.display === 'none') continue;
    var loc = events[i].querySelector('.location');
    if (!loc) continue;
    var clone = loc.cloneNode(true);
    clone.querySelectorAll('.row-icon, .map-toggle, .map-dropdown').forEach(function(el) { el.remove(); });
    var name = clone.textContent.trim();
    if (name) counts[name] = (counts[name] || 0) + 1;
  }
  return counts;
}

function buildLocationDropdown() {
  var counts = getLocationCounts();
  var sorted = Object.keys(counts).sort(function(a, b) { return counts[b] - counts[a]; });
  var top = sorted.slice(0, 40);
  if (!locationDropdown) {
    locationDropdown = document.createElement('div');
    locationDropdown.id = 'location-dropdown';
    locationDropdown.className = 'location-dropdown';
    locationDropdown.setAttribute('role', 'menu');
    locationDropdown.setAttribute('aria-label', 'Filter by venue');
    locationDropdown.addEventListener('keydown', handleLocationKeydown);
    locationBtn.setAttribute('aria-controls', 'location-dropdown');
    locationBtn.parentNode.appendChild(locationDropdown);
  }
  locationDropdown.innerHTML = '';
  for (var i = 0; i < top.length; i++) {
    var a = document.createElement('a');
    a.href = '#';
    a.setAttribute('role', 'menuitemradio');
    a.setAttribute('tabindex', '-1');
    var isActive = activeLocationFilter === top[i];
    a.setAttribute('aria-checked', isActive ? 'true' : 'false');
    a.setAttribute('aria-label', 'Filter by ' + top[i] + ', ' + counts[top[i]] + ' events');
    a.dataset.location = top[i];
    a.textContent = top[i] + ' (' + counts[top[i]] + ')';
    locationDropdown.appendChild(a);
  }
  var remaining = sorted.length - top.length;
  if (remaining > 0) {
    var more = document.createElement('span');
    more.className = 'location-more';
    more.textContent = remaining + ' more venue' + (remaining === 1 ? '' : 's');
    locationDropdown.appendChild(more);
  }
  if (filterInput.value || activeLocationFilter) {
    var clear = document.createElement('a');
    clear.href = '#';
    clear.setAttribute('role', 'menuitem');
    clear.setAttribute('tabindex', '-1');
    clear.className = 'location-clear';
    clear.textContent = 'Clear filter';
    locationDropdown.appendChild(clear);
  }
  return locationDropdown;
}

function closeLocationDropdown() {
  if (locationDropdown) locationDropdown.classList.remove('open');
  locationBtn.setAttribute('aria-expanded', 'false');
}

function openLocationDropdown(focusFirst) {
  buildLocationDropdown();
  var rect = locationBtn.getBoundingClientRect();
  var navRect = nav.getBoundingClientRect();
  locationDropdown.style.top = (rect.bottom + 4) + 'px';
  locationDropdown.style.right = (window.innerWidth - navRect.right) + 'px';
  locationDropdown.classList.add('open');
  locationBtn.setAttribute('aria-expanded', 'true');
  if (focusFirst) {
    var first = locationDropdown.querySelector('a');
    if (first) first.focus();
  }
}

locationBtn.addEventListener('click', function(e) {
  e.preventDefault();
  var isOpen = locationDropdown && locationDropdown.classList.contains('open');
  closeLocationDropdown();
  if (isOpen) return;
  openLocationDropdown();
});

locationBtn.addEventListener('keydown', function(e) {
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    var isOpen = locationDropdown && locationDropdown.classList.contains('open');
    if (!isOpen) openLocationDropdown(true);
    else {
      var first = locationDropdown.querySelector('a');
      if (first) first.focus();
    }
  }
  if (e.key === 'Escape' && activeLocationFilter) {
    e.preventDefault();
    e.stopPropagation();
    activeLocationFilter = '';
    filterEvents(filterInput.value);
  }
});

function handleLocationKeydown(e) {
  var items = Array.from(locationDropdown.querySelectorAll('a'));
  var idx = items.indexOf(document.activeElement);
  if (idx < 0) return;
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    if (idx < items.length - 1) items[idx + 1].focus();
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    if (idx > 0) items[idx - 1].focus();
    else { closeLocationDropdown(); locationBtn.focus(); }
  } else if (e.key === 'Escape') {
    e.preventDefault();
    closeLocationDropdown();
    locationBtn.focus();
  }
}

document.addEventListener('focusin', function(e) {
  if (!locationDropdown || !locationDropdown.classList.contains('open')) return;
  if (!locationDropdown.contains(e.target) && e.target !== locationBtn) {
    closeLocationDropdown();
  }
});

document.addEventListener('click', function(e) {
  if (!e.target.closest('.location-filter-wrap')) closeLocationDropdown();
  var item = e.target.closest('.location-dropdown a');
  if (!item) return;
  e.preventDefault();
  closeLocationDropdown();
  if (item.classList.contains('location-clear')) {
    activeLocationFilter = '';
  } else {
    activeLocationFilter = item.dataset.location;
  }
  filterEvents(filterInput.value);
});
