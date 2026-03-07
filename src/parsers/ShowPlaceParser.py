from parsers.GenericParser import GenericParser


class ShowPlaceParser(GenericParser):

    def collectElements(self, soup, config):
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
