# -*- coding: utf-8 -*-
# couchdb_compact Django management command.
import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from relax.couchdb import compact, shortcuts


class Command(BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('-d', '--debug',
            dest='debug', action='store_true', default=False,
            help="Don't exit until compaction has completed."),
        make_option('-a', '--compact-all',
            dest='compact_all', action='store_true', default=False,
            help='Compact all CouchDB databases.'),
        make_option('-s', '--sync',
            dest='sync', action='store_true', default=False,
            help='Run compactions synchronously.'))
    
    help = 'Compact CouchDB databases.'
    args = '[-s] [-d] [--compact-all | db_name1[, db_name2, ...]]'
    
    def handle(self, *db_names, **options):
        # Process options and arguments
        debug = options.get('debug', False)
        compact_all = options.get('compact_all', False)
        sync = options.get('sync', False)
        server = shortcuts.get_server()
        if (not db_names) and compact_all:
            db_names = list(server)
        
        # Set up logger
        root_logger_name = logging.root.name
        logging.root.name = 'couchdb_compact'
        root_logger_level = logging.root.getEffectiveLevel()
        if debug:
            logging.root.setLevel(logging.DEBUG)
        
        # Begin compaction
        for db_name in db_names:
            logging.debug('Compacting %r' % (db_name,))
            if debug or sync:
                try:
                    result = compact(db_name, poll_interval=0.4)
                except CompactionError:
                    result = False
                if not result:
                    logging.error('Error compacting %r' % (db_name,))
                else:
                    logging.debug('Successfully compacted %r' % (db_name,))
            else:
                try:
                    check_completed = compact(db_name)
                except CompactionError:
                    logging.error('Error compacting %r' % (db_name,))
                else:
                    logging.debug('Successfully began compaction of %r' % 
                        (db_name,))