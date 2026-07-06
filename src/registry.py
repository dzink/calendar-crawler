"""
Central class registry. Auto-discovers classes from parse/, transform/, and process/ directories.
"""

import os
import importlib

classes = {}

_src = os.path.dirname(os.path.abspath(__file__))
_dirs = ['parse', 'transform', 'process']

for _dir in _dirs:
    _path = os.path.join(_src, _dir)
    for _file in os.listdir(_path):
        if _file.endswith('.py') and not _file.startswith('_'):
            _name = _file[:-3]
            _module = importlib.import_module(_name)
            if hasattr(_module, _name):
                classes[_name] = getattr(_module, _name)
