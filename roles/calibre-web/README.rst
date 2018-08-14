====================
Calibre Web README
====================

This Ansible role installs Calibre Web within Internet-in-a-Box. Calibre Web is
a web app providing a clean interface for browsing, reading and downloading eBooks
using an existing Calibre database.

Access
------

If enabled and with the default settings Calibre-web should be accessible at http://box/calibre-web.
This is front-end application running under Apache2 httpd.

To login to Calibre-web enter

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
You can login using the default administration account. Then select "Configuration"
under admin panel.

Upgrading
---------
Reinstalling Calibre-web automatically upgrades to the latest version. Please backup your configuration
before reinstalling. To retain your configuration set calibre-web_provision variable to False.

You can manually upgrade while following commands:

$ cd /opt/calibre-web

$ sudo git pull

Backup Content
--------------
Calibre-web stores its configuration into SQLite database file /library/calibre-web/metadata.db.
The content is stored in various folders under /library/calibre-web. Please backup the files before
upgrading. Also set calibre-web_provision varilable to False before upgrading.

Known Issues
------------
Current implementation of the calibre-web in Internet in a box doesn't include https/SSL configuration.
Some of the administration login urls might not work.
