# Parser Configuration

Events are parsed from HTML using a config-driven system defined in `data/sources.yml`. Each source specifies how to fetch a page, how to extract fields from it, how to transform those fields, and how to post-process the resulting event list.

The pipeline is orchestrated by `CalendarFactory.getEvents()`:

1. **Parse** — extract raw field dicts from HTML
2. **Transform** — transform each field dict (dates, text cleanup, etc.)
3. **Build** — convert field dicts to Event objects
4. **Process** — filter/modify the event list

## Source structure

```yaml
sourceName:
  name: Display Name
  source:
    url: https://example.com/events
    scrollCount: 4                   # optional: scroll the page N times before parsing
  parser:
    class: Parser                    # or a subclass like ShowPlaceParser
    container: div.event             # CSS selector for each event element
    require: a.btn                   # optional: skip elements missing this selector
    fields:
      # ... field definitions
  transform:
    # ... ordered field transformation steps
  process:
    # ... post-processing on the event list
```

## Parser classes

### Parser

The default config-driven parser. Selects container elements from the page and extracts fields from each one. All behavior is defined in YAML.

### Subclassing Parser

For pages that don't fit the simple "list of identical containers" model, subclass Parser and override `collectElements`:

| Hook | Purpose | Default behavior |
|------|---------|-----------------|
| `collectElements(soup, config)` | Yield `(element, extra_fields)` pairs | Select all containers, filter by `require` |

The `extra_fields` dict is merged into the field bag before field extraction. This is how a subclass can inject context like a date heading.

**Example: ShowPlaceParser** overrides `collectElements` to walk Tumblr posts with stateful h2 date headings, yielding each `<p>` event with `{'date': currentDate}` as extra fields.

## Parser properties

### container
**Required.** CSS selector matching each event element on the page.
```yaml
container: div.eventWrapper
container: article.eventlist-event--upcoming
```

### require
Optional CSS selector. Elements that don't contain a match for this selector are skipped.
```yaml
require: a.btn-primary    # skip events without a ticket link
require: h1 a             # skip events without a linked title
```

### containerIndex
Optional list of 0-based indices. When set, only the containers at these positions are processed. Used with subclasses that iterate multiple page sections.
```yaml
containerIndex: [0, 1]    # only parse the first two containers
```

### fields
A map of field names to extraction definitions. See [Field extraction](#field-extraction).

## Field extraction

Fields extract values from each container element. Some field names map directly to event properties:

| Field name    | Event property |
|---------------|----------------|
| `title`       | summary        |
| `description` | description    |
| `link`        | link/URL       |
| `location`    | location       |
| `img`         | flyer image    |
| `imgAlt`      | flyer alt text |
| `start`       | start datetime (set by transform, not directly) |
| `end`         | end datetime (set by transform, not directly)   |

Any other field names (e.g. `date`, `time`, `ticketsLink`) are working fields available to the transform pipeline but not mapped to the event.

### Shorthand syntax

A plain string value. The simplest way to define a field.

**Text extraction** — a CSS selector returns `.get_text().strip()`:
```yaml
title: h2
date: div.eventDateList
```

**Attribute extraction** — `selector@attribute`:
```yaml
link: a@href
img: img@src
```

The selector part is optional. `@href` extracts from the container element itself.

**Fallback chain** — ` | ` (with spaces) tries multiple selectors in order:
```yaml
img: img@data-image | img@src
```

Returns the first non-empty result.

### Object syntax

For more control, use the object form.

#### selector
CSS selector to find the target element within the container. If omitted, the container element itself is used.
```yaml
description:
  selector: div.event-body
```

#### extract
How to get the value from the matched element. Default: `text`.

| Value | Behavior |
|-------|----------|
| `text` | `.get_text().strip()` |
| `paragraphs` | Paragraph-preserving text (`<p>` becomes `\n\n`, `<br>` becomes `\n`) |
| `attr:name` | HTML attribute value (e.g. `attr:href`) |

```yaml
description:
  extract: paragraphs
  removeTag: script
```

#### removeTag
Remove all instances of an HTML tag from the element before extraction.
```yaml
location:
  selector: li.address
  removeTag: a
```

#### default
Fallback value if the selector matches nothing.
```yaml
location:
  selector: span.venue
  default: "TBA"
```

#### fallback
An alternative field definition tried if the primary value is null. Can be a full field definition (with its own selector, extract, etc).
```yaml
description:
  selector: div.summary-excerpt
  extract: paragraphs
  fallback:
    selector: div.summary-content
    extract: paragraphs
```

#### index
0-based index into all selector matches. Use when a page reuses the same class for different data.
```yaml
date:
  selector: div.bm-txt-0
  index: 0
description:
  selector: div.bm-txt-0
  index: 1
  extract: paragraphs
```

#### select
Controls which matching elements are used. Default: `first`.

| Value | Behavior |
|-------|----------|
| `first` | Use the first match (default) |
| `all` | Concatenate text from all matches, joined by `separator` |

```yaml
title:
  selector: h1, h2.support
  select: all
  separator: ", "        # default: ", "
```

#### separator
Join string used with `select: all`. Default: `", "`.

## Transform pipeline

An ordered list of steps that transform the extracted fields before creating the event. Each step operates on the shared field bag (a dict of field names to values).

### Field interpolation

Several transform types support `{fieldName}` placeholders in their text/value parameters. These are replaced with the current value of the named field at runtime. Supported in: `set` (value), `append` (text), `prefix` (text), `regex` (default).

```yaml
- type: set
  target: description
  value: "{title} at {location}"
- type: regex
  target: titleTime
  pattern: '...'
  default: "{titleTime}"    # use field value as fallback
```

Defined at the source level under `transform:`. The default class is `Transformer`. For custom logic, specify a dict with `class:` and `steps:`:

```yaml
# Simple form (list of steps, uses default Transformer):
transform:
  - type: autoDate
  - type: set
    target: location
    value: My Venue

# Custom class form:
transform:
  class: MyTransformer
  steps:
    - type: autoDate
```

### autoDate

The primary date parser. Uses the `dateparser` library for flexible date parsing and a fuzzy regex for extracting start/end times from strings like "7-9pm", "doors at 8", "noon".

Time is resolved in priority order: explicit time fields > fuzzy-extracted times > defaults.

```yaml
- type: autoDate
  target: date               # field containing the date text (default: "date")
  timeField: time            # field with fuzzy time text (e.g. "Doors at 7 | $10")
  startTimeField: startTime  # field with explicit start time (e.g. "7:30 PM")
  endTimeField: endTime      # field with explicit end time (e.g. "9:30 PM")
  defaultTime: "19:00"       # fallback start time in 24h format (default: "19:00")
  defaultDuration: "2:00"    # fallback: end = start + this duration (hours:minutes)
  defaultEndTime: "23:59"    # fallback: end = same day at this time (24h format)
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `target` | no | `"date"` | Field containing the date text to parse |
| `timeField` | no | — | Field with fuzzy time text. Times are extracted via regex before the date is parsed. |
| `startTimeField` | no | — | Field with an explicit start time string (e.g. from a dedicated `<time>` element) |
| `endTimeField` | no | — | Field with an explicit end time string |
| `defaultTime` | no | `"19:00"` | Fallback start time if no time is found (24h format) |
| `defaultDuration` | no | — | Fallback end time as duration from start, e.g. `"2:00"` = 2 hours |
| `defaultEndTime` | no | — | Fallback end time as absolute time on the same day (24h format) |

If neither `timeField` nor `startTimeField` is set, fuzzy time extraction runs on the date text itself.

The date text is pre-cleaned before parsing: `|` suffixes (prices), `@` separators, end-time ranges (`- 10:30 AM`), and asterisks are stripped. Ordinals (`8th`, `1st`) are handled natively by dateparser.

The year is corrected to the nearest year (closest to today), so yearless dates like "March 15" resolve correctly near year boundaries.

### nearestYear

Append the nearest year to a date field. Useful for dates like "Saturday March 15" that lack a year.

```yaml
- type: nearestYear
  target: date                      # field to modify (default: "date")
  format: "%A %B %d"               # strptime format of the current value
  separator: " "                    # between date and year (default: "")
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `target` | no | `"date"` | Field to modify |
| `format` | no | `"%A %B %d"` | `strptime` format of the field's current value |
| `separator` | no | `""` | String between the existing value and the appended year |

### regex

Extract a capture group from a field using a regex.

```yaml
- type: regex
  target: text                      # field to search
  pattern: '(.*)\s*@\s*([^@]*)'    # regex pattern
  group: 1                          # capture group to extract (default: 0 = full match)
  store: title                      # field to store result (default: same as target)
  default: titleTime                # fallback if no match (literal or field name)
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `target` | yes | — | Field to search |
| `pattern` | yes | — | Regex pattern. Use single quotes in YAML to avoid escaping. |
| `group` | no | `0` | Capture group index (0 = full match) |
| `store` | no | same as `target` | Field to store the result |
| `default` | no | — | Fallback if the pattern doesn't match. Supports `{fieldName}` interpolation. |

### replace

Find and replace within a field.

```yaml
- type: replace
  target: date
  find: "Sept "
  replace: "Sep "
```

With regex:
```yaml
- type: replace
  target: price
  find: "\\$"
  replace: ""
  regex: true
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `target` | yes | — | Field to modify |
| `find` | yes | — | String or regex pattern to find |
| `replace` | no | `""` | Replacement string |
| `regex` | no | `false` | If true, `find` is treated as a regex pattern |

### prefix

Prepend text to a field, with an optional guard to skip values that already match a pattern.

```yaml
- type: prefix
  target: link
  text: "https://example.com"
  unless: "^https?://"
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `target` | yes | — | Field to modify |
| `text` | yes | — | Text to prepend |
| `unless` | no | — | Regex pattern. If the field's value matches, the prefix is skipped. |

### append

Append text to a field. Supports `{fieldName}` interpolation.

```yaml
# Append literal text:
- type: append
  target: description
  text: "\n\n<span class='smaller'>Crawled from example.com.</span>"

# Append another field's value:
- type: append
  target: title
  text: ", {support}"
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `target` | yes | — | Field to modify |
| `text` | yes | — | Text to append. Supports `{fieldName}` interpolation. |

### set

Set a field to a value. Supports `{fieldName}` interpolation.

```yaml
- type: set
  target: location
  value: Metro Gallery

- type: set
  target: description
  value: "{title} at {location}"
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `target` | yes | — | Field to set |
| `value` | yes | — | Value to assign. Supports `{fieldName}` interpolation. |

### copy

Copy one field's value to another field.

```yaml
- type: copy
  target: text
  store: description
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `target` | yes | — | Field to copy from |
| `store` | yes | — | Field to copy to |

### join

Concatenate multiple fields into a new field. Empty fields are skipped.

```yaml
- type: join
  fields: [link, ticketsLink]
  store: description
  separator: " , tickets: "
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `fields` | yes | — | List of field names to concatenate |
| `store` | yes | — | Field to store the result |
| `separator` | no | `""` | String between parts |

### cut

Remove all occurrences of a regex pattern from a field.

```yaml
- type: cut
  target: date
  pattern: '\s*\|.*'
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `target` | yes | — | Field to modify |
| `pattern` | yes | — | Regex pattern to remove |

### removeOrdinals

Strip ordinal suffixes (1st, 2nd, 3rd, 4th) from numbers in a field.

```yaml
- type: removeOrdinals
  target: date
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `target` | yes | — | Field to modify |

### collapseWhitespace

Collapse whitespace in a field. Three modes based on which options are set:

```yaml
# Collapse all whitespace to nothing:
- type: collapseWhitespace
  target: location

# Collapse to a separator string:
- type: collapseWhitespace
  target: title
  separator: " | "

# Trim only (leading/trailing whitespace):
- type: collapseWhitespace
  target: title
  trim: true
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `target` | yes | — | Field to modify |
| `separator` | no | `""` | Replace whitespace runs with this string |
| `trim` | no | `false` | If true (and no separator), only strip leading/trailing whitespace |

### collapseParagraphs

Normalize whitespace while preserving paragraph structure. Horizontal whitespace collapses to a single space. Newlines collapse to a maximum of 2 (one blank line between paragraphs).

```yaml
- type: collapseParagraphs
  target: description
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `target` | yes | — | Field to modify |

## Process pipeline

Process steps run on the full event list after all events have been built. Defined at the source level under `process:`. The default class is `Processor`.

```yaml
# Simple form (list of steps, uses default Processor):
process:
  - type: rejectEvents
    pattern:
      location: (Ottobar|Red Emma's)

# Custom class form:
process:
  class: MyProcessor
  steps:
    - type: rejectEvents
      pattern:
        summary: (Taylor Swift .*)
```

### rejectEvents

Remove events matching a pattern. The pattern is a dict of field names to regex patterns. An event is rejected if any field matches.

```yaml
- type: rejectEvents
  pattern:
    location: (Ottobar|Red Emma's)
    summary: (Taylor Swift .*)
```

| Property | Required | Description |
|----------|----------|-------------|
| `pattern` | yes | Dict of `{field: regex}` pairs |
