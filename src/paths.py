import sys
import os

_src = os.path.dirname(os.path.abspath(__file__))
for _sub in ['', 'pipeline', 'fetch', 'parse', 'transform', 'process', 'db', 'providers', 'event']:
    sys.path.append(os.path.join(_src, _sub))
