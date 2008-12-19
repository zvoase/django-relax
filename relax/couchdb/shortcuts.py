import couchdb

try:
    from django.conf import settings
except ImportError:
    settings = None

from relax import settings


def get_server(server_url='http://127.0.0.1:5984/'):
    """Return a CouchDB server instance based on Django project settings."""
    return couchdb.client.Server(
        server_url if server_url else settings._('COUCHDB_SERVER'))

def get_db(db_name, server_url='http://127.0.0.1:5984/'):
    """Return a CouchDB database instance, given its name."""
    return get_server(server_url)[db_name]

def get_doc(doc_id, db_name, server_url='http://127.0.0.1:5984/', rev=None):
    """Return a CouchDB document, given its ID, revision and database name."""
    db = get_server(server_url)[db_name]
    if rev:
        headers, response = db.resource.get(doc_id, rev=rev)
        return couchdb.client.Document(response)
    return db[doc_id]

def get_or_create_db(db_name, server_url='http://127.0.0.1:5984/'):
    """Return an (optionally existing) CouchDB database instance."""
    server = get_server(server_url)
    if db_name in server:
        return server[db_name]
    return server.create(db_name)