#!python3./.venv/bin/python3

"""
Sync pending events to all configured calendar providers.

Usage:
    python provider-export.py
    python provider-export.py -d          # dry run
    python provider-export.py -p google   # only sync google providers
    python provider-export.py -n 10       # sync at most 10 events per provider
"""

import sys
sys.path.append('./src')
import paths

import yaml
import argparse
from Factory import CalendarFactory
from CalendarProvider import CalendarProvider
from CalendarLogger import logger, addLoggerArgsToParser, buildLogger


def main():
    config = loadConfig('./data/options.yml')
    options = parseArguments(config)
    buildLogger(options)

    calendarConfigs = loadConfig('./data/calendars.yml')
    secrets = loadConfig('./data/secrets.yml')
    factory = CalendarFactory(options, config, secrets)

    for calendarKey in calendarConfigs:
        calendarConfig = calendarConfigs.get(calendarKey)
        providers = factory.providers(calendarKey, calendarConfig)

        if options.provider:
            providers = [p for p in providers if p.config.get('type') in options.provider]

        for provider in providers:
            pending = provider.getPendingEvents()
            if options.after:
                pending = CalendarProvider.filterAfter(pending, options.after)
            if options.limit:
                pending = CalendarProvider.limit(pending, options.limit)
            synced = provider.syncPending(pending=pending, dryRun=options.dry_run)
            print('%s: %d events %s via %s' % (
                calendarKey,
                synced,
                'would sync' if options.dry_run else 'synced',
                type(provider).__name__,
            ))


def parseArguments(config):
    parser = argparse.ArgumentParser(description='Sync pending events to calendar providers')
    addLoggerArgsToParser(parser, config.get('logging', {}))
    parser.add_argument('-d', '--dry-run', help='Show what would be synced without syncing.', action='store_true', default=False)
    parser.add_argument('-p', '--provider', help='Only sync the given provider type(s).', action='append', default=None)
    parser.add_argument('-n', '--limit', help='Maximum number of events to sync per provider.', type=int, default=None)
    parser.add_argument('-a', '--after', help='Only sync events starting after this date (YYYY-MM-DD).', default=None)
    return parser.parse_args()


def loadConfig(filename):
    try:
        with open(filename, 'r') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        return {}


if __name__ == '__main__':
    main()
