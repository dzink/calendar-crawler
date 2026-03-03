# calendar-export.py

Exports crawled events from the event database to ICS calendar files and a
static HTML agenda page.

## Usage

```bash
python3 calendar-export.py [options]
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `-s`, `--source` | all | Only export events from the given source(s). Repeatable. |
| `-o`, `--output` | `./dist/assets/ics/events.ics` | Path for the combined ICS file. |
| `-a`, `--after` | today | Only events after this date (YYYY-MM-DD). |
| `-b`, `--before` | none | Only events before this date (YYYY-MM-DD). |
| `--html` | `./dist/index.html` | Output path for the HTML agenda. Use `"none"` to skip. |
| `--base-url` | (see code) | Base URL used to build subscribe links and meta tags. |

### Examples

```bash
# Default export (today onward, all sources)
python3 calendar-export.py

# Specific source and date range
python3 calendar-export.py -s "Ottobar" -a 2026-03-01 -b 2026-04-01

# ICS only, no HTML
python3 calendar-export.py --html none

# Custom base URL for deploy
python3 calendar-export.py --base-url https://example.com/shows
```

## Output

### ICS files (`dist/assets/ics/`)

- `events.ics` — all events in a single subscribable calendar
- `<source>.ics` — one calendar per source (e.g. `ottobar.ics`, `showPlace.ics`)

### HTML (`dist/index.html`)

A self-contained static page with inlined CSS and JS. Assets (images, un-inlined
copies of CSS/JS) are copied to `dist/assets/`.

## HTML template

Source files live in `html-template/`:

- `index.html` — page template with `{{placeholders}}`
- `assets/css/minimal.css` — styles
- `assets/js/agenda.js` — all client-side logic

### Template placeholders

| Placeholder | Replaced with |
|-------------|---------------|
| `{{content}}` | Event `<section>` elements grouped by day |
| `{{source_ics_links}}` | `<li>` links to per-source ICS files |
| `{{base_url}}` | Value of `--base-url` (used in OG/Twitter meta tags) |
| `{{webcal_ics}}` | `webcal://` subscribe link |
| `{{google_ics}}` | Google Calendar add-by-URL link |
| `{{outlook_ics}}` | Outlook web add-by-URL link |
| `{{office365_ics}}` | Office 365 web add-by-URL link |
| `{{styles}}` | Inlined `<style>` block (minified) |
| `{{scripts}}` | Inlined `<script>` block (minified) |

### Minification

CSS and JS are minified by simple regex-based minifiers in `calendar-export.py`.
The JS minifier strips `//` line comments, which means **`//` must not appear
inside JS string literals**. Use `String.fromCharCode(47, 47)` or the `_https`
variable instead. The minifier also strips block comments (`/* ... */`), except
from the inlined build — the header comment in `agenda.js` is preserved in the
source but stripped from the built output.

## Per-event "add to calendar"

Each event's `<details>` element carries data attributes used by the client-side
add-to-calendar dropdown:

| Attribute | Source |
|-----------|--------|
| `data-title` | `event.summary` |
| `data-start` | `event.startDate` as `YYYY-MM-DDTHH:MM:SS` |
| `data-end` | `event.endDate` (omitted if missing; JS defaults to 23:59:59) |
| `data-location` | `event.location` (omitted if missing) |
| `data-url` | `event.link` (omitted if missing) |

The description paragraph is marked with a `data-desc` attribute so JS can read
its text content for calendar descriptions.

The dropdown offers four options:
1. **Download .ics** — generates a blob with `text/calendar` MIME and triggers download
2. **Google Calendar** — opens Google's event creation URL
3. **Outlook** — opens Outlook web's event composer
4. **Yahoo Calendar** — opens Yahoo's event creation URL

A single shared dropdown DOM element is reused across all events to keep the page
light (500+ events typical).

## Build order

The export runs in this order to avoid the HTML asset copy (`shutil.rmtree`)
from deleting ICS files:

1. `getSourceList()` — collect source names/counts (no file writes)
2. `buildHtml()` + `writeHtml()` — generate HTML, copy template assets to `dist/`
3. `writeCalendar()` — write combined `events.ics`
4. `writeSourceCalendars()` — write per-source ICS files
