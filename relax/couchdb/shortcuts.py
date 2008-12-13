try:
    from django.conf import settings
except ImportError:
    settings = None

if not getattr(settings, 'configured', False):
    settings = object()

def get_server(url='http://localhost:5984/'):
    """Return a CouchDB server instance based on Django project settings."""
    host = getattr(settings, 'COUCHDB_SERVER', url)
    return couchdb.client.Server(host)