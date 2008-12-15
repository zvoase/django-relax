try:
    from django.conf import settings as djangosettings
except ImportError:
    djangosettings = None


class NonExistentSetting(Exception):
    
    def __init__(self, attr):
        Exception.__init__(self, 'Setting %r does not exist.' % (attr,))


COUCHDB_SERVER = 'http://localhost:5984/'
VIEW_SERVER_HOST = 'localhost:5936'


def _(attr, *args):
    if hasattr(djangosettings, attr):
        return getattr(djangosettings, attr)
    elif attr in globals():
        return globals().get(attr)
    elif args:
        return args[0]
    else:
        raise NonExistentSetting(attr)