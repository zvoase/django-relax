====================
:mod:`relax.couchdb`
====================

.. module:: relax.couchdb
	:synopsis: Tools for working directly with CouchDB from Python.
.. moduleauthor:: Zachary Voase <zack@biga.mp>

This module contains several useful features on top of the
`couchdb-python <http://couchdb-python.googlecode.com>` library which are of
interest to those working with CouchDB from Python. Therefore, there are very
few Django-specific utilities in this module. Features such as replication and
compaction are, however, present, as well as helpers for manipulating canonical
database specifiers.

:func:`relax.couchdb.specifier_to_db` -- Convert specifier to DB string
=======================================================================

.. function:: relax.couchdb.specifier_to_db(db_specifier)
	
	This function accepts a database specifier in a custom format, and returns
	either the name of the database (if it is local) or the URL to the database
	(if it is remote). This is in a format acceptable to CouchDB, and so the
	returned string may then be used for database compaction, replication,
	querying, etc.
	
	The format is as follows for local databases::
		
		local:<database_name>
	
	Where ``<database_name>`` is (obviously) the name of the database. Local
	databases get their information from the CouchDB server configured in the
	project's ``settings.py`` file. If one is not configured, the default of
	http://localhost:5984 is used. For remote databases::
	
		remote:<host>:<port_number>:<database_name>
	
	In this instance, a host and port number are required, in addition to the
	name of the database. Note that ``remote:127.0.0.1:5984:<db_name>`` is
	equivalent to ``local:<db_name>``; :func:`relax.couchdb.specifier_to_db`
	will recognise this and return the appropriate result.
	
	:param db_specifier: Canonical database specifier (see above)
	:type db_specifier: string
	:rtype: database name or URL (string)

:func:`relax.couchdb.db_to_specifier` -- Convert DB string to specifier
=======================================================================

.. function:: relax.couchdb.db_to_specifier(db_string)

	This function accepts a database string as either a raw database name or as
	a URL with a HTTP scheme, and returns a local or remote database specifier
	as would normally be taken by :func:`specifier_to_db`.
	
	:param db_string: Database string
	:type db_string: string
	:rtype: Canonical database specifier (string)