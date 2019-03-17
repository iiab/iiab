=============
Gitea README
=============

This Ansible role installs Gitea - a self-hosted Git service written in Go.

Using It
--------

Gitea should be accessible at: http://box/gitea

Configuration
-------------

Gitea has been configured to work with SQLite; it can also be used with MySQL or
PostgreSQL. If you want to use it with a different database, change the 
``DB_TYPE`` property in ``/etc/gitea/app.ini`` [1] and add one of the following 
lines to the ``[Unit]`` section of ``/etc/systemd/system/gitea.service`` [2]:

* MySQL: ``After=mysqld.service``
* PostgreSQL: ``After=postgresql.service``

[1] Prior to installing Gitea, instead edit: ``/opt/iiab/iiab/roles/gitea/templates/app.ini.j2``

[2] Prior to installing Gitea, instead edit: ``/opt/iiab/iiab/roles/gitea/templates/gitea.service.j2``

Documentation
-------------

Further info on configuring: `https://docs.gitea.io <https://docs.gitea.io/>`_
