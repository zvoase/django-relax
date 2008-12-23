# -*- coding: utf-8 -*-

import logging
import time
import urlparse

import couchdb

from relax import DEFAULT_FORMATTER
from relax.couchdb import (get_server_from_specifier, get_db_from_specifier,
    specifier_to_db, shortcuts)


class CompactionError(Exception):
    pass


def compact(db_spec, poll_interval=0):
    
    """
    Compact a CouchDB database with optional synchronicity.
    
    The ``compact`` function will compact a CouchDB database stored on an
    running CouchDB server. By default, this process occurs *asynchronously*,
    meaning that the compaction will occur in the background. Often, you'll want
    to know when the process has completed; for this reason, ``compact`` will
    return a function which, when called, will return the state of the
    compaction. If it has completed, ``True`` will be returned; otherwise,
    ``False``. This may be called multiple times.
    
    Alternatively, you may opt to run ``compact`` in synchronous mode, for
    debugging or profiling purposes. If this is the case, an optional keyword
    argument ``poll_interval`` is accepted, which should be a number (in
    seconds) representing the time to take between polls. A sensible default
    may be around 0.5 (seconds).
    
    Because this function operates on database specifiers, you can choose to
    operate on the local server or any remote server.
    """
    
    server = get_server_from_specifier(db_spec)
    db = get_db_from_specifier(db_spec)
    # Get logger
    logger = logging.getLogger('relax.couchdb.compact')
    logger.info('Pre-compact size of %r: %s' % (db_spec,
        repr_bytes(db.info()['disk_size']),))
    logger.debug('POST ' + urlparse.urljoin(db.resource.uri + '/', '_compact'))
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
            logger.debug(
                'Polling database to check if compaction has completed')
            logger.debug('GET ' + db.resource.uri + '/')
            db_info = db.info()
            completed = not db_info.get('compact_running', False)
            if completed and db_info.get('disk_size', None):
                logger.info('Post-compact size of %r: %s' % (db_spec,
                    repr_bytes(db_info['disk_size'])))
            return completed
        return check_completed
    # Synchronous compaction
    elif poll_interval > 0:
        logger.debug(
            'Polling database to check if compaction has completed')
        logger.debug('GET ' + db.resource.uri + '/')
        # Shows whether compaction is running or not.
        running = db.info().get('compact_running', False)
        # Poll the running state of the compaction.
        while running:
            time.sleep(poll_interval)
            logger.debug(
                'Polling database to check if compaction has completed')
            logger.debug('GET ' + db.resource.uri + '/')
            running = db.info().get('compact_running', False)
        size_after = db.info().get('disk_size', None)
        if size_after:
            logger.info('Post-compact size of %r: %s' % (db_spec,
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