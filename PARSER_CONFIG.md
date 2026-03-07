# Parser Configuration

Events are parsed from HTML using a config-driven system defined in `data/sources.yml`. Each source specifies how to fetch a page, how to extract events from it, and how to post-process the results.

## Source structure

```yaml
sourceName:
  name: Display Name
  source:
    url: https://example.com/events
    scrollCount: 4                   # optional: scroll the page N times before parsing
  parser:
    class: GenericParser             # or a subclass like ShowPlaceParser
    container: div.event             # CSS selector for each event element
    require: a.btn                   # optional: skip elements missing this selector
    fields:
      # ... field definitions
    tamper:
      # ... ordered processing steps
  postTasks:
    # ... post-processing on the event list
```

## Parser classes

### GenericParser

The default config-driven parser. Selects container elements from the page, extracts fields from each one, runs the tamper pipeline, and builds events. All behavior is defined in YAML.

### Subclassing GenericParser

For pages that don't fit the simple "list of identical containers" model, subclass GenericParser and override one or more hooks:

| Hook | Purpose | Default behavior |
|------|---------|-----------------|
| `collectElements(soup, config)` | Yield `(element, extra_fields)` pairs | Select all containers, filter by `require` |
| `beforeTamper(fields)` | Transform fields after extraction | No-op |
| `afterTamper(fields)` | Transform fields after tamper pipeline | No-op |

The `extra_fields` dict is merged into the field bag before field extraction. This is how a subclass can inject context like a date heading.

Subclasses inherit `acceptsConfig = True` from GenericParser, so CalendarFactory automatically passes the parser config.

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

### tamper
An ordered list of transformation steps. See [Tamper pipeline](#tamper-pipeline).

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
| `start`       | start datetime (set by tamper, not directly) |
| `end`         | end datetime (set by tamper, not directly)   |

Any other field names (e.g. `date`, `time`, `ticketsLink`) are working fields available to the tamper pipeline but not mapped to the event.

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

## Tamper pipeline

An ordered list of steps that transform the extracted fields before creating the event. Each step operates on the shared field bag (a dict of field names to values).

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
| `default` | no | — | Fallback if the pattern doesn't match. If the value matches an existing field name, that field's value is used; otherwise it's treated as a literal string. |

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

Append one field's value onto another. Only runs if both fields have values.

```yaml
- type: append
  target: title
  field: support
  separator: ", "
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `target` | yes | — | Field to modify |
| `field` | yes | — | Field whose value to append |
| `separator` | no | `", "` | String between the two values |

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

## Post-tasks

Post-tasks run on the full event list after all events have been parsed. They are shared across all parser types.

### addBoilerplateToDescriptions

Append text to every event's description.

```yaml
- type: addBoilerplateToDescriptions
  text: <span class='smaller'>Crawled from https://example.com.</span>
```

| Property | Required | Description |
|----------|----------|-------------|
| `text` | yes | HTML/text to append |

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

### setLocationAddress

Set the location on all events that don't already have one.

```yaml
- type: setLocationAddress
  text: Metro Gallery
```

| Property | Required | Description |
|----------|----------|-------------|
| `text` | yes | Location string |

### setColors

Set the calendar color for all events.

```yaml
- type: setColors
  color: default
```

| Property | Required | Description |
|----------|----------|-------------|
| `color` | yes | Color name |

### prefixLinks

Prepend a base URL to all event links that don't already have a full URL.

```yaml
- type: prefixLinks
  text: https://www.example.com
```

| Property | Required | Description |
|----------|----------|-------------|
| `text` | yes | Base URL to prepend |

### prefixDescriptionsWithLinks

Prepend each event's link URL to its description text. No configuration options.

```yaml
- type: prefixDescriptionsWithLinks
```

### prefixDescriptionsWithFlyer

Prepend each event's flyer image as a link in the description. No configuration options.

```yaml
- type: prefixDescriptionsWithFlyer
```

### setAbsoluteEndDateTime

Set the end time on all events to a fixed time of day. Use `autoDate`'s `defaultEndTime` instead when possible.

```yaml
- type: setAbsoluteEndDateTime
  hour: 23
  minute: 59
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `hour` | no | `23` | Hour (24h format) |
| `minute` | no | `59` | Minute |

### setDefaultTimeLength

Set a default duration on events that don't have an end time. Use `autoDate`'s `defaultDuration` instead when possible.

```yaml
- type: setDefaultTimeLength
  hour: 2
  minute: 0
```

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `hour` | no | `2` | Hours |
| `minute` | no | `0` | Minutes |
