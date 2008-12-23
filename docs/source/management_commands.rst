================================
django-relax Management Commands
================================

.. rubric:: Project-level tools for administering CouchDB databases.

The management commands documented here are called from a project's
``manage.py`` module, and as such represent common operations which involve an
entire Django project.


:mod:`relax.management.commands.couchdb_compact` -- Database compaction
=======================================================================

.. module:: relax.management.commands.couchdb_compact
    :synopsis: Compact one or more databases.
.. moduleauthor:: Zachary Voase <zack@biga.mp>

.. program:: couchdb_compact

This command can take a number of database specifiers and will perform database
compaction on them. This involves removing old revisions and unnecessary or
otherwise redundant data, optimizing disk usage and improving server
performance. For more information on CouchDB compaction, consult the CouchDB
wiki page on `compaction <http://wiki.apache.org/couchdb/Compaction>`_.

.. note::
	
	The database specifiers which this command takes must be of a form
	acceptable to :func:`relax.couchdb.get_db_string`. Consult this
	function's documentation for more information.

This command accepts several options:

.. cmdoption:: -s, --sync
	
	If this option is given, then compaction will run *synchronously*. By
	default, a compaction process will be started on the server and then the
	command will exit. This tells the command to keep running until the process
	on the server side has stopped. Successful compaction of the database is
	detected by the polling of the server at regular intervals of 0.4 seconds.

.. cmdoption:: -a, --compact-all
	
	If specified, this option will compact every database on the server. This
	should be given instead of the list of databases; if some database names
	are given, the command will compact all databases on the server anyway.

.. seealso::
	
	Module :mod:`relax.couchdb.compact`
		A module for carrying out compaction programmatically.
	
	Function :func:`relax.couchdb.get_db_string`
		The function which processes the database specifiers.


:mod:`relax.management.commands.couchdb_replicate` -- Database replication
==========================================================================

.. module:: relax.management.commands.couchdb_replicate
	:synopsis: Replicate one database to another (optionally-existing) database.
.. moduleauthor:: Zachary Voase <zack@biga.mp>

.. program:: couchdb_replicate

This command will replicate a CouchDB database. Replication is a process whereby
data is copied from one CouchDB database to another. However, it is more
sophisticated than this; CouchDB only copies the differences between two
databases, meaning that replication can be efficiently used to maintain a
cluster of CouchDB servers for distribution of read load amongst several
machines.

This command accepts as its arguments two database specifiers. These must be in
the same form as those for :mod:`relax.management.commands.couchdb_compact`.
Therefore, it is recommended that you consult the documentation for
:func:`relax.couchdb.get_db_string`.

.. seealso::
	
	Module :mod:`relax.couchdb.replicate`
		A module for programmatically replicating CouchDB databases.
	
	Function :func:`relax.couchdb.get_db_string`
		The function which processes the database specifiers.