# -*- coding: utf-8 -*-

import datetime
import logging
import re
import urlparse

from couchdb import client

from relax.couchdb.shortcuts import get_server


class ReplicationError(Exception):
    
    def __init__(response_headers, result):
        Exception.__init__(self,
            'Error in replication session %s.' % (result['session_id'],))
        self.response_headers = response_headers
        self.result = result


def get_db_string(db_spec):
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
    info = db_spec.split(':')
    # Local database specified by local:<db_name>
    if info[0] == 'local':
        return info[1]
    # Remote DB specified by remote:<host>:<port_num>:<db_name>
    elif info[0] == 'remote':
        host, port_num, db_name = info[1:]
        return 'http://%s:%s/%s' % (host, port_num, db_name)
    else:
        return db_spec


def replicate_existing(source_db, target_db):
    """Replicate an existing database to another existing database."""
    server = get_server()
    logging.debug('POST ' + server.resource.uri + '/_replicate')
    resp_headers, resp_body = server.resource.post(path='/_replicate',
        content=json.dumps({
            'source': get_db_string(source_db),
            'target': get_db_string(target_db)}))
    result = resp_body['history'][0]
    logging.info('Replication %s' % (resp_body['session_id']))
    logging.info('Replication started: ' + result['start_time'])
    logging.info('Replication finished: ' + result['end_time'])
    result['start_time'] = datetime.datetime.strptime(result['start_time'],
        '%a, %d %b %Y %H:%M:%S GMT')
    result['end_time'] = datetime.datetime.strptime(result['end_time'],
        '%a, %d %b %Y %H:%M:%S GMT')
    timedelta = result['end_time'] - result['start_time']
    if timedelta.days:
        logging.info('Replication took %d days and %.2f seconds.' % (
            timedelta.days,
            timedelta.seconds + (timedelta.microseconds * (1e-6))))
    else:
        logging.info('Replication took %.2f seconds.' % (
            timedelta.seconds + (timedelta.microseconds * (1e-6))))
    result['ok'] = resp_body['ok']
    result['session_id'] = resp_body['session_id']
    result['source_last_seq'] = resp_body['source_last_seq']
    if not result['ok']:
        logging.error('Replication failed.')
        raise ReplicationError(result['session_id'], resp_headers, result)
    return result

def replicate(source_db, target_db):
    """Replicate one existing database to another (optionally existing) DB."""
    source = get_db_string(source_db)
    target_db_url = get_db_string(target_db)
    # If the target is remote, the db_name will be the path of the URL.
    # Otherwise, target_db_url will be the name of the database.
    if target_db_url.startswith('http://'):
        scheme, netloc, path = urlparse.urlparse(target_db_url)[:3]
        db_name = path.lstrip('/')
        server_url = '%s://%s' % (scheme, netloc)
        target = shortcuts.get_or_create_db(db_name, server_url=server_url)
    else:
        target = shortcuts.get_or_create_db(target_db_url)
    return replicate_existing(source.resource.uri, target.resource.uri)