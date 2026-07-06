import json
import os
import yaml


class Config:
    def __init__(self, configDir=None):
        if configDir is None:
            projectRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            configDir = os.path.join(projectRoot, 'config')
        self.configDir = configDir

    def pathTo(self, filename):
        """Return the full path to a file in the config directory."""
        return os.path.join(self.configDir, filename)

    def _load(self, filename):
        """Load a YAML or JSON config file. Returns empty dict if file not found."""
        filepath = os.path.join(self.configDir, filename)
        try:
            with open(filepath, 'r') as file:
                if filename.endswith('.json'):
                    return json.load(file) or {}
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            return {}

    def loadSources(self):
        return self._load('sources.yml')

    def loadCalendars(self):
        return self._load('calendars.yml')

    def loadOptions(self):
        return self._load('options.yml')

    def loadSecrets(self):
        return self._load('secrets.yml')

    def loadToken(self):
        return self._load('token.json')

    def loadCredentials(self):
        return self._load('credentials.json')
