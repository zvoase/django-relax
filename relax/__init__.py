# -*- coding: utf-8 -*-

# Import ``simplejson`` library as ``json``, one way or another!
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        try:
            from django.utils import simplejson as json
        except ImportError:
            json = None

import logging


DEFAULT_FORMATTER = logging.Formatter(
    '%(asctime)s: %(levelname)s (%(name)s): %(message)s', # Log format string
    '%a, %d %b %Y %H:%M:%S %Z' # Date format string (HTTP-compatible for GMT)
)