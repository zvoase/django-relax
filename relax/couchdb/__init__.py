# -*- coding: utf-8 -*-

import re
import urlparse

from relax import settings
from relax.couchdb import shortcuts


# These regex's may look complicated and weird, but that's because they *are*.
LOCAL_RE = re.compile(r'^local:'
    r'(?P<database>[A-Za-z][A-Za-z0-9\_\$\(\)\+\-\/]+)$')
REMOTE_RE = re.compile(r'^remote:'
    r'(?P<hostname>([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9-]+[A-Za-z0-9])|'
    r'(([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9-]+[A-Za-z0-9])\.)+([A-Za-z0-9]|'
    r'[A-Za-z0-9][A-Za-z0-9-]+[A-Za-z0-9])):'
    r'(?P<portnum>\d+):(?P<database>[A-Za-z][A-Za-z0-9\_\$\(\)\+\-\/]+)$')
PLAIN_RE = re.compile(r'^(?P<database>[A-Za-z][A-Za-z0-9\_\$\(\)\+\-\/]+)$')
URL_RE = re.compile(r'^(http:\/\/)(?P<hostname>([A-Za-z0-9]|[A-Za-z0-9]'
    r'[A-Za-z0-9-]+[A-Za-z0-9])|(([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9-]+'
    r'[A-Za-z0-9])\.)+([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9-]+[A-Za-z0-9])):'
    r'(?P<portnum>\d+)\/(?P<database>[A-Za-z][A-Za-z0-9\_\$\(\)\+\-\/]+)$')


def specifier_to_db(db_spec):
    """
    Return the database string for a database specifier.
    
    The database specifier takes a custom format for specifying local and remote
    databases. A local database is specified by the following format:
        
        local:<db_name>
    
    For example, a database called 'sessions' would be specified by the string
    ``'local:sessions'``. Remote databases are specified like this:
    
        remote:<host>:<port_num>:<db_name>
    
    For example, a database called 'log' on the server 'dev.example.com' at port
    number 5984 would be specified by ``'remote:dev.example.com:5984:log'``.
    
    These specifiers are translated into strings acceptable to CouchDB; local
    specs are turned into the database name alone, and remote specs are turned
    into ``'http://host:port/db_name'`` URLs.
    """
    local_match = LOCAL_RE.match(db_spec)
    remote_match = REMOTE_RE.match(db_spec)
    plain_match = PLAIN_RE.match(db_spec)
    # If this looks like a local specifier:
    if local_match:
        return local_match.groupdict()['database']
    # If this looks like a remote specifier:
    elif remote_match:
        # A fancy 'unpacking'...
        hostname, portnum, database = map(remote_match.groupdict().get,
            ('hostname', 'portnum', 'database'))
        local_url = settings._('COUCHDB_SERVER', 'http://127.0.0.1:5984/')
        localhost, localport = urlparse.urlparse(local_url)[1].split(':')
        # If it's local, return a local DB string.
        if (localhost == hostname) and (localport == portnum):
            return database
        # Otherwise, get a remote URL.
        return 'http://%s:%s/%s' % (hostname, portnum, database)
    # If this looks like a plain database name, return it.
    elif plain_match:
        return plain_match.groupdict()['database']
    # Throw a wobbly.
    raise ValueError('Invalid database spec: %r' % (db_spec,))


def db_to_specifier(db_string):
    """
    Return the database specifier for a database string.
    
    This accepts a database name or URL, and returns a database specifier in the
    format accepted by ``specifier_to_db``. It is recommended that you consult
    the documentation for that function for an explanation of the format.
    """
    local_match = PLAIN_RE.match(db_string)
    remote_match = URL_RE.match(db_string)
    # If this looks like a local specifier:
    if local_match:
        return 'local:' + local_match.groupdict()['database']
    # If this looks like a remote specifier:
    elif remote_match:
        # Just a fancy way of getting 3 variables in 2 lines...
        hostname, portnum, database = map(remote_match.groupdict().get,
            ('hostname', 'portnum', 'database'))
        local_url = settings._('COUCHDB_SERVER', 'http://127.0.0.1:5984/')
        localhost, localport = urlparse.urlparse(local_url)[1].split(':')
        # If it's the local server, then return a local specifier.
        if (localhost == hostname) and (localport == portnum):
            return 'local:' + database
        # Otherwise, prepare and return the remote specifier.
        return 'remote:%s:%s:%s' % (hostname, portnum, database)
    # Throw a wobbly.
    raise ValueError('Invalid database string: %r' % (db_string,))

def get_server_from_db(db_string):
    """Return a CouchDB server instance from a database string."""
    local_match = PLAIN_RE.match(db_string)
    remote_match = URL_RE.match(db_string)
    # If this looks like a local specifier:
    if local_match:
        return shortcuts.get_server()
    elif remote_match:
        hostname, portnum, database = map(remote_match.groupdict().get,
            ('hostname', 'portnum', 'database'))
        local_url = settings._('COUCHDB_SERVER', 'http://127.0.0.1:5984/')
        localhost, localport = urlparse.urlparse(local_url)[1].split(':')
        # If it's the local server, then return a local specifier.
        if (localhost == hostname) and (localport == portnum):
            return shortcuts.get_server()
        return shortcuts.get_server(
            server_url=('http://%s:%s' % (hostname, portnum)))
    raise ValueError('Invalid database string: %r' % (db_string,))

def get_server_from_specifier(db_spec):
    """Return a CouchDB server instance from a database specifier."""
    return get_server_from_db(specifier_to_db(db_spec))

def get_db_from_db(db_string):
    """Return a CouchDB database instance from a database string."""
    server = get_server_from_db(db_string)
    local_match = PLAIN_RE.match(db_string)
    remote_match = URL_RE.match(db_string)
    # If this looks like a local specifier:
    if local_match:
        return server[local_match.groupdict()['database']]
    elif remote_match:
        return server[remote_match.groupdict()['database']]
    raise ValueError('Invalid database string: %r' % (db_string,))

def get_db_from_specifier(db_spec):
    """Return a CouchDB database instance from a database specifier."""
    return get_db_from_db(specifier_to_db(db_spec))

def ensure_specifier_exists(db_spec):
    """Make sure a DB specifier exists, creating it if necessary."""
    local_match = LOCAL_RE.match(db_spec)
    remote_match = REMOTE_RE.match(db_spec)
    plain_match = PLAIN_RE.match(db_spec)
    if local_match:
        db_name = local_match.groupdict().get('database')
        server = shortcuts.get_server()
        if db_name not in server:
            server.create(db_name)
        return True
    elif remote_match:
        hostname, portnum, database = map(remote_match.groupdict().get,
            ('hostname', 'portnum', 'database'))
        server = shortcuts.get_server(
            server_url=('http://%s:%s' % (hostname, portnum)))
        if database not in server:
            server.create(database)
        return True
    elif plain_match:
        db_name = plain_match.groupdict().get('database')
        server = shortcuts.get_server()
        if db_name not in server:
            server.create(db_name)
        return True
    return False

def ensure_db_exists(db_string):
    """Make sure a DB string exists, creating it if necessary."""
    return ensure_specifier_exists(db_to_specifier(db_string))