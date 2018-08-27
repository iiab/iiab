==================
Calibre-Web README
==================

This Ansible role installs Calibre-Web in Internet-in-a-Box (we'll call it
"calibre-web" from here on down).  The calibre-web server provides a clean
interface for browsing, reading and downloading e-books using an existing
Calibre database.

Access
------

After installation you can access calibre-web at `http://box:8083` or
`http://box/calibre-web` (in future we may consider `http://box/books`).
You can log in with administrative account:

 Username: Admin

 Password: changeme

If the default configuration is not found, calibre-web server creates a
new settings file with calibre-web's own default administrative account:

 Username: admin

 Password: admin123

Backend
-------

You can manage the backend calibre-web server manually with these commands:

  systemctl enable calibre-web

  systemctl start calibre-web

  systemctl status calibre-web

  systemctl stop calibre-web

Configuration
-------------

To configure calibre-web, first login as 'Admin'.  Then select 'Configuration'
under the admin panel.

The default calibre-web settings are stored under
'/library/calibre-web/config/app.db' database file. The calibre-web stores
its eBook information in calibre database '/library/calibre-web/metadata.db'
file.

Upgrading
---------

Reinstalling calibre-web automatically upgrades to the latest version.
Please backup your configuration before reinstalling.  To retain your
configuration set `calibreweb_provision` variable to False.

You can manually upgrade using 'git' command:

$ cd /opt/calibre-web

$ sudo git pull

Backup Your Content
-------------------

calibre-web stores e-books and various configuration settings under
/library/calibre-web.  Please backup this folder before upgrading.  Also set
`calibreweb_provision` variable to False before upgrading to prevent the
Provision script from over-writting your settings.

Known Issues
------------

Trying to access a empty public bookshelf causes a system error.

As of August 2018, calibre-web doesn't include Calibre's e-book conversion
functionality (Calibre itself allows teachers to convert between PDF, epub, txt
etc — to permit reading on a wider array client devices and client software).
