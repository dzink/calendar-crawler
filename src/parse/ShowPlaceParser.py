"""
ShowPlaceParser

Parses the ShowPlace Tumblr blog (baltshowplace.tumblr.com).

The page contains multiple Tumblr posts, each with a div.body-text that lists
events grouped under h2 date headings:

    <h2>Saturday, March 7, 2026</h2>
    <p>Band Name. 8PM, $10 @ Venue</p>
    <p>Other Band. 9PM, $5 @ Other Venue</p>
    <h2>Sunday, March 8, 2026</h2>
    <p>...</p>

This parser walks the children of each post's body-text, tracking the current
date heading and yielding each <p> as an event element with the date injected
as an extra field. Field extraction and transforms are handled by the factory.
"""

from Parser import Parser


class ShowPlaceParser(Parser):

    def collectElements(self, soup, config):
        """Walk h2/p siblings in each post, yielding (p_element, {'date': heading})."""
        container = config.get('container')
        containerIndex = config.get('containerIndex')

        containers = self._select(soup, container)
        if containerIndex is not None:
            containers = [containers[i] for i in containerIndex if i < len(containers)]

        for el in containers:
            scope = el.select_one('div.body-text')
            if not scope:
                continue

            currentDate = None
            for child in scope.children:
                if not hasattr(child, 'name') or child.name is None:
                    continue
                if child.name == 'h2':
                    currentDate = child.get_text().strip()
                elif child.name == 'p' and currentDate:
                    if child.get_text().strip():
                        yield child, {'date': currentDate}
