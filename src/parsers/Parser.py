"""
Parser

Config-driven event field extractor. Reads HTML and yields field dicts
using CSS selectors defined in sources.yml.

Subclasses can override collectElements() to change how events are
collected from the page (e.g. ShowPlaceParser's stateful h2/p walking).

See PARSER_CONFIG.md in the project root for full config syntax.
"""

from bs4 import BeautifulSoup
from CalendarLogger import logger
import ParserUtils
import copy
import re


class Parser:

    acceptsConfig = True

    def __init__(self, sourceTitle, parserConfig=None):
        self.sourceTitle = sourceTitle
        self.parserConfig = parserConfig or {}

    def parseFields(self, html):
        """Extract fields from HTML. Yields one dict per event."""
        config = self.parserConfig
        fieldDefs = config.get('fields', {})
        soup = self.makeSoup(html)

        for el, extra in self.collectElements(soup, config):
            try:
                fields = dict(extra)
                for name, defn in fieldDefs.items():
                    fields[name] = self._extractField(el, defn)
                yield fields
            except Exception as e:
                eventText = ParserUtils.replaceWhitespaceWithPipes(el.get_text())
                logger.exception("Exception occurred in " + eventText)

    # --- Subclass hook ---

    def collectElements(self, soup, config):
        """Yield (element, extra_fields) for each item to parse.
        Override in subclasses to change how events are collected."""
        container = config.get('container')
        require = config.get('require')
        elements = self._select(soup, container)
        for el in elements:
            if require and not el.select_one(require):
                continue
            yield el, {}

    # --- HTML utilities ---

    def makeSoup(self, html):
        return BeautifulSoup(html, features="html.parser")

    def removeTagFromElement(self, element, tag):
        for match in element.find_all(tag):
            match.extract()
        return element

    def getDescriptionText(self, element):
        if element is None:
            return ''
        el = copy.copy(element)
        for p in el.find_all('p'):
            p.insert_before('\n\n')
        for br in el.find_all('br'):
            br.insert_before('\n')
            br.decompose()
        text = el.get_text()
        text = re.sub(r'[^\S\n]*\n[^\S\n]*', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[^\S\n]{2,}', ' ', text)
        return text.strip()

    # --- Field extraction ---

    def _select(self, soup, selector):
        if not selector:
            return []
        return soup.select(selector)

    def _extractField(self, el, defn):
        """Extract a field value from an element based on its definition."""
        if defn is None:
            return None

        if isinstance(defn, str):
            return self._extractShorthand(el, defn)

        selector = defn.get('selector')
        separator = defn.get('separator', ', ')
        select = defn.get('select', 'first')

        if select == 'all' and selector:
            targets = el.select(selector)
            if not targets:
                return defn.get('default')
            extract = defn.get('extract', 'text')
            parts = [self._extractValue(t, extract) for t in targets]
            return separator.join(p for p in parts if p)

        index = defn.get('index')
        if index is not None and selector:
            targets = el.select(selector)
            target = targets[index] if len(targets) > index else None
        else:
            target = el.select_one(selector) if selector else el

        if target is None:
            return defn.get('default')

        removeTag = defn.get('removeTag')
        if removeTag:
            target = copy.copy(target)
            self.removeTagFromElement(target, removeTag)

        extract = defn.get('extract', 'text')
        value = self._extractValue(target, extract)

        if value is None:
            fallback = defn.get('fallback')
            if fallback:
                return self._extractField(el, fallback)
            return defn.get('default')

        return value

    def _extractShorthand(self, el, shorthand):
        """Parse shorthand like 'h1.title', 'a@href', 'img@src | img@data-src'."""
        if ' | ' in shorthand:
            for part in shorthand.split(' | '):
                result = self._extractShorthand(el, part.strip())
                if result:
                    return result
            return None

        if '@' in shorthand:
            selector, attr = shorthand.rsplit('@', 1)
            target = el.select_one(selector) if selector else el
            if target is None:
                return None
            return target.get(attr)

        target = el.select_one(shorthand)
        if target is None:
            return None

        return target.get_text().strip()

    def _extractValue(self, target, extract):
        """Extract a value from an element based on extract type."""
        if extract == 'text':
            return target.get_text().strip()
        if extract == 'paragraphs':
            return self.getDescriptionText(target)
        if extract.startswith('attr:'):
            return target.get(extract[5:])
        return target.get_text().strip()
