============
Gitea README
============

This Ansible role installs Gitea — a self-hosted Git service written in Go.

Using It
--------

Gitea should be accessible at: http://box/gitea

Gitea repositories can be cloned using either HTTP or SSH. When cloning with 
HTTP, the clone URL will start with ``http://box.lan/gitea/``. SSH clone URLs 
start with ``gitea@box.lan``.

Installation and Setup
----------------------

Simply run ``cd /opt/iiab/iiab`` then ``sudo ./runrole gitea`` to install
Gitea. After installing, Gitea will be live at http://box/gitea

The first time you access the Gitea web interface, the home page will appear. 
Clicking on "Register" or "Sign In" in the upper right corner will take you to 
the setup page. The recommended settings have been configured for you, but you 
can change them if you want. For example, you may want to change the site title 
to match the name of your organization.

After finishing the setup process, you will be directed to a page where you can 
create a user account. The first account created after setting up Gitea will be 
an admin account. You can also create an admin account from the setup page 
under "Administrator Account Settings."

Configuration
-------------

Gitea has been configured to work with SQLite; it can also be used with MySQL or
PostgreSQL. If you want to use it with a different database, change the 
``DB_TYPE`` property in ``/etc/gitea/app.ini`` [1] and add one of the following 
lines to the ``[Unit]`` section of ``/etc/systemd/system/gitea.service`` [2]:

* MySQL: ``After=mysqld.service``
* PostgreSQL: ``After=postgresql.service``

For MySQL and PostgreSQL, you need to specify the server address, the database 
name, and the user credentials that Gitea will use to access the database. 
**Make sure the user exists on the database server first.**

[1] Prior to installing Gitea, instead edit: ``/opt/iiab/iiab/roles/gitea/templates/app.ini.j2``

[2] Prior to installing Gitea, instead edit: ``/opt/iiab/iiab/roles/gitea/templates/gitea.service.j2``

Documentation
-------------

- Further info on configuring: `https://docs.gitea.io <https://docs.gitea.io/>`_
- Gitea supporting materials [best CS learning for developing countries?] `#1556 <https://github.com/iiab/iiab/issues/1556>`_
