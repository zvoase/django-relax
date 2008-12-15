import couchdb

try:
    from django.conf import settings
except ImportError:
    settings = None

from relax import settings


def get_server(server_url=None):
    """Return a CouchDB server instance based on Django project settings."""
    return couchdb.client.Server(
        server_url if server_url else settings._('COUCHDB_SERVER'))

def get_db(db_name, server_url=None):
    """Return a CouchDB database instance, given its name."""
    return get_server(server_url)[db_name]

def get_doc(doc_id, db_name, server_url=None, rev=None):
    """Return a CouchDB document, given its ID, revision and database name."""
    db = get_server(server_url)[db_name]
    if rev:
        headers, response = db.resource.get(doc_id, rev=rev)
        return couchdb.client.Document(response)
    return db[doc_id]