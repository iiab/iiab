====================
Calibre-web README
====================

This Ansible role installs Calibre-web in Internet-in-a-Box. Calibre-web server
provides a clean interface for browsing, reading and downloading eBooks
using an existing Calibre database.

Access
------

After installation you can access Calibre-web at `http://box/calibre-web` using the
following IIAB calibre-web administration account.

  Username: Admin

  Password: changme

If the default configuration is not found calibre-web server creates a new settings file
with calibre-web default administration account.

 Username: admin

 Password: admin123

Backend
--------
You can manage the backend Calibre-web server manually with the following commands:

  systemctl enable calibre-web

  systemctl start calibre-web

  systemctl status calibre-web

  systemctl stop calibre-web

Configuration
-------------
To configure calibre-web, first login as 'Admin'. Then select 'Configuration'
under the admin panel.


The default calibre-web settings are stored under '/library/calibre-web/config/app.db'
database file. The calibre-web stores its eBook information in calibre database
 '/library/calibre-web/metadata.db' file.

Upgrading
---------
Reinstalling Calibre-web automatically upgrades to the latest version. Please backup your configuration
before reinstalling. To retain your configuration set `calibreweb_provision` variable to False.

You can manually upgrade using 'git' command:

$ cd /opt/calibre-web

$ sudo git pull

Backuping Content
--------------
Calibre-web stores eBooks and various configuration settings under /library/calibre-web.
Please backup this folder before upgrading. Also set `calibreweb_provision` variable to
False before upgrading to prevent the Provision script from over-writting your settings.

Known Issues
------------
Trying to access a empty public bookshelf causes a system error.

Current implementation of the calibre-web in Internet in a box doesn't include ebook converter program.
