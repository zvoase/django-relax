# -*- coding: utf-8 -*-

import datetime
import logging
import re
import urlparse

from couchdb import client

from relax import DEFAULT_FORMATTER, json, settings
from relax.couchdb import ensure_specifier_exists, specifier_to_db, shortcuts


class ReplicationError(Exception):
    
    def __init__(self, server_error_args):
        Exception.__init__(self, 'Error in replication session.')
        self.response_status = server_error_args[0][0]
        self.response_reason = server_error_args[0][1][0]
        self.response_body = json.loads(server_error_args[0][1][1])


class ReplicationFailure(Exception):
    
    def __init__(self, response_headers, result):
        Exception.__init__(self, 'Replication failed.')
        self.response_headers = response_headers
        self.result = result


def replicate_existing(source_db, target_db):
    """Replicate an existing database to another existing database."""
    # Get the server from which to manage the replication.
    server = shortcuts.get_server()
    logger = logging.getLogger('relax.couchdb.replicate')
    logger.debug('POST ' + urlparse.urljoin(server.resource.uri, '/_replicate'))
    source, target = specifier_to_db(source_db), specifier_to_db(target_db)
    logger.debug('Source DB: %s' % (source,))
    logger.debug('Target DB: %s' % (target,))
    try:
        resp_headers, resp_body = server.resource.post(path='/_replicate',
            content=json.dumps({'source': source, 'target': target}))
    except couchdb.client.ServerError, exc:
        logger.error('Replication failed.')
        raise ReplicationError(exc.args)
    result = resp_body['history'][0]
    if resp_body['ok']:
        logger.info('Replication %s... successful!' % (
            resp_body['session_id'][:6],))
        logger.info('Replication started: ' + result['start_time'])
        logger.info('Replication finished: ' + result['end_time'])
        result['start_time'] = datetime.datetime.strptime(result['start_time'],
            '%a, %d %b %Y %H:%M:%S GMT')
        result['end_time'] = datetime.datetime.strptime(result['end_time'],
            '%a, %d %b %Y %H:%M:%S GMT')
        timedelta = result['end_time'] - result['start_time']
        if timedelta.days:
            logger.info('Replication took %d days and %.2f seconds.' % (
                timedelta.days,
                timedelta.seconds + (timedelta.microseconds * (1e-6))))
        else:
            logger.info('Replication took %.2f seconds.' % (
                timedelta.seconds + (timedelta.microseconds * (1e-6))))
        # Prepare the 'result' dictionary.
        result['ok'] = resp_body['ok']
        result['session_id'] = resp_body['session_id']
        result['source_last_seq'] = resp_body['source_last_seq']
        # Info-log the number of docs read/written and checked/found.
        if result['docs_read'] == 1:
            docs_read = '1 document read'
        else:
            docs_read = '%d documents read' % (result['docs_read'],)
        if result['docs_written'] == 1:
            docs_written = '1 document written'
        else:
            docs_written = '%d documents written' % (result['docs_written'],)
        if result['missing_checked'] == 1:
            missing_checked = 'Checked for 1 missing document, found %d.' % (
                result['missing_found'],)
        else:
            missing_checked = 'Checked for %d missing documents, found %d.' % (
                result['missing_checked'], result['missing_found'],)
        logging.info('%s, %s' % (docs_read, docs_written))
        logging.info(missing_checked)
        return result
    else:
        logger.error('Replication %s... failed.' % (
            resp_body['session_id'][:6],))
        result['ok'] = resp_body['ok']
        result['session_id'] = resp_body['session_id']
        result['source_last_seq'] = resp_body['source_last_seq']
        raise ReplicationFailure(resp_headers, result)


def replicate(source_spec, target_spec):
    """Replicate one existing database to another (optionally existing) DB."""
    ensure_specifier_exists(target_spec)
    return replicate_existing(source_spec, target_spec)