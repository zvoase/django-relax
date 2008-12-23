"""
Utility module for getting hold of Django setting in a quick 'n' easy way.
"""

try:
    from django.conf import settings as djangosettings
except ImportError:
    djangosettings = None


class NonExistentSetting(Exception):
    
    def __init__(self, attr):
        Exception.__init__(self, 'Setting %r does not exist.' % (attr,))


def _(attr, *args):
    if hasattr(djangosettings, attr):
        return getattr(djangosettings, attr)
    elif attr in globals():
        return globals.get(*((attr,) + args))
    elif args:
        return args[0]
    else:
        raise NonExistentSetting(attr)