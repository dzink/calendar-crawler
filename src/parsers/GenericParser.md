# GenericParser

A config-driven parser that extracts events from HTML using CSS selectors and a tamper pipeline. Defined entirely in `sources.yml` — no Python code needed.

## Structure

```yaml
sourceName:
  name: Source Name
  source:
    url: https://example.com/events
  parser:
    class: GenericParser
    container: div.event            # CSS selector for each event element
    require: h1 a                   # optional: skip elements missing this selector
    fields:
      # ... field definitions
    tamper:
      # ... ordered processing steps
  postTasks:
    # ... post-processing (shared with all parsers)
```

## Fields

Fields extract values from each container element. The field name determines how it maps to the event object:

| Field name    | Event property |
|---------------|----------------|
| `title`       | summary        |
| `description` | description    |
| `link`        | link/URL       |
| `location`    | location       |
| `img`         | flyer image    |
| `imgAlt`      | flyer alt text |
| `start`       | start datetime (set by tamper, not directly) |
| `end`         | end datetime (set by tamper, not directly)   |

Any other field names (e.g. `date`, `time`, `support`) are working fields available to the tamper pipeline but not mapped to the event directly.

### Shorthand syntax

The simplest way to define a field — a plain string value.

**Text extraction** — CSS selector, returns `.get_text().strip()`:
```yaml
title: h1.event-title
date: span.date
```

If the selector contains "description", it automatically uses paragraph-preserving extraction (`getDescriptionText`).

**Attribute extraction** — use `@` to extract an HTML attribute:
```yaml
link: a.event-link@href
img: img@src
```

**Fallback chain** — use ` | ` (with spaces) to try multiple selectors:
```yaml
img: img@data-image | img@src
```

Returns the first non-empty result.

### Object syntax

For more control, use the object form:

```yaml
location:
  selector: li.address       # CSS selector (omit to use the container element itself)
  removeTag: a               # remove all instances of this tag before extraction
  extract: text              # extraction mode (see below)
  default: "Unknown"         # fallback if selector matches nothing
  fallback:                  # alternative field definition if value is null
    selector: span.location
```

**Extract modes:**
- `text` (default) — `.get_text().strip()`
- `description` — paragraph-preserving text (converts `<p>` to `\n\n`, `<br>` to `\n`)
- `attr:name` — extract an HTML attribute (e.g. `attr:href`)

**Extracting from the container itself** (no child selector):
```yaml
description:
  extract: description
  removeTag: script          # can still remove tags before extraction
```

**Selecting by index** — when there are multiple matches and you need a specific one:
```yaml
timestamp:
  selector: div.bm-txt-0
  index: 0                   # 0-based index into all matches (default: first match)
description:
  selector: div.bm-txt-0
  index: 1
  extract: description
```

**Selecting all matches** — concatenate text from all matching elements:
```yaml
title:
  selector: h1, h2.support   # CSS selector (can use commas for multiple tag types)
  all: true                   # select all matches, not just first
  separator: ", "             # join text with this (default: ", ")
```

Returns text from all matches in DOM order, joined by separator.

## Tamper pipeline

An ordered list of steps that transform the extracted fields before creating the event. Each step operates on the shared field bag.

### parseDate

Concatenate fields into a date string and store with its format.

```yaml
- type: parseDate
  fields: [date, startTime]        # fields to concatenate
  format: "%A, %B %d, %Y%I:%M %p" # strptime format for the result
  target: start                    # store as "start" (also sets "startFormat")
  separator: ""                    # optional, between fields (default: "")
```

### parseDateFuzzy

Extract start/end times from a fuzzy time string (e.g. "7-9pm", "doors at 8", "noon").

```yaml
- type: parseDateFuzzy
  fields: [date, time]             # date fields + time field
  format: "%B %d %Y %I:%M%p"      # strptime format for the result
  timeField: time                  # which field has the fuzzy time (default: "time")
  defaultTime: "19:00"             # fallback start time in 24h (default: "19:00")
  defaultEndTime: "22:00"          # optional fallback end time in 24h
  separator: " "                   # between parts (default: " ")
```

### nearestYear

Append the nearest year to a date field (for dates without a year).

```yaml
- type: nearestYear
  target: date                     # field to modify (default: "date")
  format: "%A %B %d"              # strptime format of the current value
  separator: " "                   # between date and year (default: "")
```

### regex

Extract or match a pattern in a field.

```yaml
- type: regex
  target: description              # field to search
  pattern: '(\d+)(:\d\d)'         # regex pattern (use single quotes in YAML to avoid escaping)
  group: 0                        # capture group to extract (default: 0 = full match)
  store: time                     # field to store result (default: same as target)
  default: "7:00"                 # fallback if no match
```

### replace

Find and replace within a field.

```yaml
- type: replace
  target: date
  find: "Sept "
  replace: "Sep "

# With regex:
- type: replace
  target: startRaw
  find: "$"
  replace: "PM"
  regex: true
```

### prefix

Prepend text to a field, with optional guard.

```yaml
- type: prefix
  target: link
  text: "https://example.com"
  unless: "^https?://"            # skip if value already matches this regex
```

### append

Append one field's value onto another.

```yaml
- type: append
  target: title                   # field to modify
  field: support                  # field whose value to append
  separator: ", "                 # between the two values (default: ", ")
```

Only appends if both fields have values.

### join

Concatenate multiple fields into a new field.

```yaml
- type: join
  fields: [date, time]
  store: startRaw                 # field to store result
  separator: " "                  # between parts (default: "")
```

Skips empty fields.

### cut

Remove a regex pattern from a field.

```yaml
- type: cut
  target: title
  pattern: '\s*\(.*?\)'          # remove parenthetical text
```

### removeOrdinals

Strip ordinal suffixes (1st, 2nd, 3rd, 4th) from numbers in a field.

```yaml
- type: removeOrdinals
  target: date
```

### collapseWhitespace

Collapse whitespace in a field.

```yaml
# Collapse all whitespace to nothing:
- type: collapseWhitespace
  target: location

# Collapse to a separator:
- type: collapseWhitespace
  target: location
  separator: " "

# Trim only (leading/trailing):
- type: collapseWhitespace
  target: title
  trim: true
```

### collapseParagraphs

Normalize whitespace while preserving paragraph structure. Collapses spaces to single space, newlines to max 2.

```yaml
- type: collapseParagraphs
  target: description
```
