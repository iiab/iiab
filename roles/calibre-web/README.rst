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
