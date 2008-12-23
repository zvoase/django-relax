# -*- coding: utf-8 -*-
# couchdb_compact Django management command.
import logging
import time

from django.core.management.base import BaseCommand, make_option

from relax import DEFAULT_FORMATTER, settings
from relax.couchdb import db_to_specifier, specifier_to_db, compact, shortcuts


class Command(BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('-a', '--compact-all',
            dest='compact_all', action='store_true', default=False,
            help='Compact all CouchDB databases in the configured server.'),
        make_option('-s', '--sync',
            dest='sync', action='store_true', default=False,
            help='Run compactions synchronously.'))
    
    help = 'Compact CouchDB databases.'
    args = '[-s] [--compact-all | db_spec1[, db_spec2, ...]]'
    
    def handle(self, *db_specs, **options):
        # Process options and arguments
        compact_all = options.get('compact_all', False)
        sync = options.get('sync', False)
        if (not db_specs) and compact_all:
            local_server = shortcuts.get_server()
            db_specs = map(db_to_specifier, list(local_server))
        # Set up logger
        logger = logging.getLogger('relax.couchdb.compact')
        handler = logging.StreamHandler()
        handler.setFormatter(DEFAULT_FORMATTER)
        logger.handlers = [handler]
        if settings._('DEBUG', True):
            logger.setLevel(logging.DEBUG)
        logger.propagate = False
        # Begin compaction
        for db_spec in db_specs:
            logger.debug('Compacting %r' % (db_spec,))
            if sync:
                try:
                    result = compact.compact(db_spec, poll_interval=0.4)
                except compact.CompactionError:
                    result = False
                if not result:
                    logger.error('Error compacting %r' % (db_spec,))
                else:
                    logger.info('Successfully compacted %r' % (db_spec,))
            else:
                try:
                    check_completed = compact.compact(db_spec)
                except compact.CompactionError:
                    logger.error('Error compacting %r' % (db_spec,))
                else:
                    logger.info('Successfully began compaction of %r', db_spec)