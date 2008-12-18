# -*- coding: utf-8 -*-

import re

from couchdb import client

from relax.couchdb.shortcuts import get_server


def get_server_url(server_string):
    info = server_string.split(':')
    # Local database specified by local:<db_name>
    if info[0] == 'local':
        return info[1]
    # Remote DB specified by remote:<host>:<port_num>:<db_name>
    elif info[0] == 'remote':
        host, port_num, db_name = info[1:]
        return 'http://%s:%s/%s' % (host, port_num, db_name)


def _replicate_existing(source_db, target_db):
    server = get_server()
    # TODO: POST to /_replicate on the server with the JSON data:
    #     {'source': source_db, 'target': target_db}
    # This will begin the replication process.