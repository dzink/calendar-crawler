"""
test-env.py — Verify the environment is set up correctly.

Checks:
  - Python version
  - Virtual environment is active
  - Required packages are importable
  - src/ path setup works
  - Data files are accessible
  - Config files parse correctly
"""

import sys
import os

passed = 0
failed = 0

def check(label, condition, detail=''):
    global passed, failed
    if condition:
        print('  OK  %s' % label)
        passed += 1
    else:
        print('  FAIL  %s%s' % (label, (' — ' + detail) if detail else ''))
        failed += 1

print('Environment checks:\n')

# Python version
v = sys.version_info
check('Python 3.8+', v.major == 3 and v.minor >= 8,
      'got %d.%d' % (v.major, v.minor))

# Virtual environment
in_venv = sys.prefix != sys.base_prefix
check('Running in virtual environment', in_venv,
      'sys.prefix = %s' % sys.prefix)

# Working directory
cwd = os.getcwd()
check('Working directory has src/', os.path.isdir('src'),
      'cwd = %s' % cwd)

# src path setup
sys.path.append('./src')
try:
    import paths
    check('src/paths.py loads', True)
except Exception as e:
    check('src/paths.py loads', False, str(e))

# Core imports
core_modules = [
    ('yaml', 'pyyaml'),
    ('bs4', 'beautifulsoup4'),
    ('dateparser', 'dateparser'),
    ('tinydb', 'tinydb'),
]

for module, package in core_modules:
    try:
        __import__(module)
        check('import %s' % module, True)
    except ImportError:
        check('import %s' % module, False, 'pip install %s' % package)

# Internal modules
internal_modules = ['CalendarLogger', 'StringUtils', 'Factory', 'Pipeline']
for mod in internal_modules:
    try:
        __import__(mod)
        check('import %s' % mod, True)
    except ImportError as e:
        check('import %s' % mod, False, str(e))

# Data directory
check('data/ directory exists', os.path.isdir('data'))

# Config files
from Config import Config
cfg = Config()
for name, loader in [('sources.yml', cfg.loadSources), ('calendars.yml', cfg.loadCalendars)]:
    try:
        data = loader()
        check('parse config/%s' % name, bool(data), 'file not found or empty')
    except Exception as e:
        check('parse config/%s' % name, False, str(e))

# Summary
print('\n%d passed, %d failed' % (passed, failed))
sys.exit(1 if failed else 0)
