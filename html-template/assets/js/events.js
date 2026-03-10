/*
 * events.js — Event details, row icons, truncation, URLs, copy, maps.
 */

/* ===================== Event details ===================== */

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
    truncateDescription(det);
    scrollIntoViewSmooth(det);
  }
}, true);

/* ===================== Description truncation ===================== */

/* Truncate long descriptions with a fade and "see all" toggle */
function truncateDescription(det) {
  var desc = det.querySelector('.description');
  if (!desc || desc.nextElementSibling && desc.nextElementSibling.classList.contains('desc-toggle')) return;
  var em = parseFloat(getComputedStyle(desc).fontSize);
  if (desc.scrollHeight <= em * 25) return;
  desc.classList.add('desc-truncated');
  var link = document.createElement('a');
  link.href = '#';
  link.className = 'desc-toggle simple-link';
  link.textContent = 'see all';
  link.addEventListener('click', function(e) {
    e.preventDefault();
    if (desc.classList.contains('desc-truncated')) {
      desc.classList.remove('desc-truncated');
      desc.classList.add('desc-expanded');
      link.textContent = 'see less';
      scrollIntoViewSmooth(desc);
    } else {
      desc.classList.remove('desc-expanded');
      desc.classList.add('desc-truncated');
      link.textContent = 'see all';
      scrollIntoViewSmooth(desc, 'start');
    }
  });
  desc.after(link);
}

/* ===================== Anchor links ===================== */

/* Handle anchor links to sections/details (e.g. sidebar "About" links) */
document.addEventListener('click', function(e) {
  var link = e.target.closest('a[href^="#"]');
  if (!link) return;
  var id = link.getAttribute('href').slice(1);
  var target = document.getElementById(id);
  if (!target) return;
  e.preventDefault();
  if (target.tagName === 'DETAILS') target.open = true;
  var top = target.getBoundingClientRect().top + window.scrollY - navHeight() - 10;
  window.scrollTo({ top: top, behavior: 'instant' });
});

/* ===================== URL truncation & copy button ================== */

agenda.querySelectorAll('.details a').forEach(function(link) {
  var text = link.textContent.trim();
  if (text.indexOf('https:') !== 0 && text.indexOf('http:') !== 0) return;
  link.textContent = text.replace(/^https?:\x2f\x2f/, '');
  link.classList.add('url-truncate');
  link.classList.add('url-stripped');
  var icon = document.createElement('span');
  icon.className = 'external-icon';
  icon.setAttribute('aria-hidden', 'true');
  link.after(icon);
  // Adds a copy button.
  // var btn = document.createElement('button');
  // btn.className = 'copy-url';
  // btn.title = 'Copy URL';
  // btn.setAttribute('aria-label', 'Copy URL');
  // link.after(btn);
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
  sec.innerHTML = '<button class="copy-event btn secondary-btn icon-btn" aria-label="Copy event details" title="Copy event details"><span class="hidden">Copy Details</span></button>'
    + '<button class="add-to-cal btn primary-btn" aria-haspopup="menu" aria-expanded="false">add to calendar</button>';
  det.appendChild(sec);
}, true);

/* ===================== Flyer image loader ========================== */

agenda.addEventListener('click', function(e) {
  var btn = e.target.closest('.flyer-toggle');
  if (!btn) return;
  var flyer = btn.closest('.flyer');
  var expanded = btn.getAttribute('aria-expanded') === 'true';
  if (expanded) {
    var img = flyer.querySelector('.flyer-img');
    if (img) img.remove();
    btn.setAttribute('aria-expanded', 'false');
    btn.textContent = 'See Flyer';
  } else {
    var img = document.createElement('img');
    img.src = btn.dataset.src;
    img.alt = btn.dataset.alt || '';
    img.className = 'flyer-img';
    flyer.appendChild(img);
    btn.setAttribute('aria-expanded', 'true');
    btn.textContent = 'Hide Flyer';
    img.onload = function() { scrollIntoViewSmooth(flyer); };
  }
});

/* ===================== Map links ====================================== */

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
    clone.querySelectorAll('.row-icon, .map-toggle, .map-dropdown').forEach(function(el) { el.remove() });
    dd.innerHTML = buildMapLinks(clone.textContent);
    trigger.after(dd);
    dd.classList.add('open');
    return;
  }
  if (mapDropdown && !e.target.closest('.map-dropdown') && !e.target.closest('.map-toggle')) closeMap();
});

/* Inject [map] toggle after each location element */
agenda.querySelectorAll('.location:not(.no-map)').forEach(function(loc) {
  var btn = document.createElement('a');
  btn.href = '#';
  btn.className = 'map-toggle';
  btn.textContent = '[map options]';
  loc.append(btn);
});
