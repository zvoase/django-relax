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