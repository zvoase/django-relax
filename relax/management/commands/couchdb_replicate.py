# -*- coding: utf-8 -*-
# couchdb_compact Django management command.

import logging
import os
import re

from django.conf import settings
from django.core.management.base import BaseCommand

from relax import DEFAULT_FORMATTER, json, settings
from relax.couchdb import replicate, shortcuts
from relax.utils import logrotate


class Command(BaseCommand):
    
    help = 'Replicate CouchDB databases.'
    args = 'source_specifier target_specifier'
        
    def handle(self, source_spec, target_spec, *args, **options):
        # Set up logger
        logger = logging.getLogger('relax.couchdb.replicate')
        handler = logging.StreamHandler()
        handler.setFormatter(DEFAULT_FORMATTER)
        logger.addHandler(handler)
        if settings._('DEBUG', True):
            logger.setLevel(logging.DEBUG)
        logger.propagate = False
        # Replicate the databases
        logger.info('Beginning replication.')
        try:
            replicate.replicate(source_spec, target_spec)
        except replicate.ReplicationFailure, exc:
            # If there was an error, write the error output from CouchDB to a
            # rotated replication log file.
            log_filename = logrotate('replication.log')
            logger.error('Dumping JSON error information to "%s"' % (
                log_filename,))
            fp = open(log_filename, 'w')
            try:
                fp.write('response_headers = %s' % (
                    json.dumps(exc.response_headers),))
                fp.write(os.linesep * 2)
                fp.write('result = %s' % (
                    json.dumps(exc.response_headers),))
                fp.write(os.linesep)
            finally:
                fp.close()