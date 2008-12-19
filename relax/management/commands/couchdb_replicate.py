# -*- coding: utf-8 -*-
# couchdb_compact Django management command.

import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from relax import json
from relax.couchdb import replicate, shortcuts


class Command(BaseCommand):
    
    help = 'Replicate CouchDB databases.'
    args = 'source_specifier target_specifier'
    
    def handle(self, source_spec, target_spec):
        
        # Set up logger
        root_logger_name = logging.root.name
        logging.root.name = 'couchdb_replicate'
        
        # Replicate the databases
        logging.info('Beginning replication.')
        try:
            replicate.replicate(source_spec, target_spec)
        except replicate.ReplicationError, exc:
            logging.error('Writing error log to "replication.log"')
            fp = open('replication.log', 'w')
            try:
                fp.write(json.dumps(exc.response_headers))
                fp.write(os.linesep)
                fp.write(json.dumps(exc.result))
                fp.write(os.linesep)
            finally:
                fp.close()
        
        # Reset root logger
        logging.root.name = root_logger_name
