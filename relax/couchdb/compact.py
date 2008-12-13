# -*- coding: utf-8 -*-

import logging
import time

import couchdb

from relax.couchdb import shortcuts


class CompactionError(Exception):
    pass


def compact(db_name, poll_interval=0, server=None):
    
    """
    Compact a CouchDB database with optional synchronicity.
    
    The ``compact`` function will compact a CouchDB database stored on an
    optionally specified (running) CouchDB server. By default, this process
    occurs *asynchronously*, meaning that the compaction will occur in the
    background. Often, you'll want to know when the process has completed; for
    this reason, ``compact`` will return a function which, when called, will
    return the state of the compaction. If it has completed, ``True`` will
    be returned; otherwise, ``False``. This may be called multiple times.
    
    Alternatively, you may opt to run ``compact`` in synchronous mode, for
    debugging or profiling purposes. If this is the case, an optional keyword
    argument ``poll_interval`` is accepted, which should be a number (in
    seconds) representing the time to take between polls. A sensible default
    may be around 0.5 (seconds).
    
    If you wish to use a server other than the one specified by the
    ``COUCHDB_SERVER`` setting in your Django project settings, you may
    optionally pass in an argument, ``server``, with an instance of
    ``couchdb.client.Server``, representing a running CouchDB server.
    """
    
    server = shortcuts.get_server() if (not server) else server
    db = server[db_name]
    logging.info('Pre-compact size of %r: %s' % (db_name,
        repr_bytes(db.info()['disk_size']),))
    logging.debug('POST ' + db.resource.uri + '/_compact')
    # Start compaction process by issuing a POST to '/<db_name>/_compact'.
    resp_headers, resp_body = db.resource.post('/_compact')
    # Asynchronous compaction
    if not poll_interval:
        if not (resp_body.get('ok', False) and
            resp_headers['status'] == '202'):
            err = CompactionError('Compaction of %r failed.')
            # Give the exception some useful information.
            err.response = (resp_headers, resp_body)
            raise err
        # Return a function which, when called, will return whether or not the
        # compaction process is still running.
        def check_completed():
            logging.debug(
                'Polling database to check if compaction has completed')
            logging.debug('GET ' + db.resource.uri + '/')
            db_info = db.info()
            completed = not db_info.get('compact_running', False)
            if completed and db_info.get('disk_size', None):
                logging.info('Post-compact size of %r: %s' % (db_name,
                    repr_bytes(db_info['disk_size'])))
        return check_completed
    # Synchronous compaction
    elif poll_interval > 0:
        logging.debug(
            'Polling database to check if compaction has completed')
        logging.debug('GET ' + db.resource.uri + '/')
        # Shows whether compaction is running or not.
        running = db.info().get('compact_running', False)
        # Poll the running state of the compaction.
        while running:
            time.sleep(poll_interval)
            logging.debug(
                'Polling database to check if compaction has completed')
            logging.debug('GET ' + db.resource.uri + '/')
            running = db.info().get('compact_running', False)
        size_after = db.info().get('disk_size', None)
        if size_after:
            logging.info('Post-compact size of %r: %s' % (db_name,
                repr_bytes(size_after)))
        return True
    else:
        raise ValueError('Poll interval must be greater than zero.')

def repr_bytes(bytes):
    sizes = 'B KB MB GB TB PB'.split()
    size_index = 0
    while bytes > 1024:
        bytes /= 1024.0
        size_index += 1
    return '%.2f %s' % (bytes, sizes[size_index])