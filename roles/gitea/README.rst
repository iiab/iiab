=============
Gitea README
=============

This Ansible role installs Gitea - a self-hosted Git service written in Go.

Using It
--------

Gitea should be accessible at http://box/gitea/.

Configuration
-------------

Gitea has been configured to work with MySQL; it can also be used with SQLite or
Postgres. If you want to use it with a different database, change the 
``DB_TYPE`` property in ``app.ini`` and change the line ``After=mysqld.service``
in ``gitea.service`` to one of the following:

* SQLite: comment it out.
* Postgres: ``After=postgresql.service``

Further information about configuring Gitea can be found at the
`documentation <https://docs.gitea.io/en-us/>`.
