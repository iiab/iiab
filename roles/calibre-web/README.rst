==================
Calibre-Web README
==================

Calibre-Web provides a clean interface for browsing, reading and downloading
e-books using an existing Calibre database.  Teachers can add upload e-books,
adjust e-book metadata, and create custom book collections ("bookshelves"):
https://github.com/janeczku/calibre-web#about

This Ansible role installs Calibre-Web as part of your Internet-in-a-Box, as a
possible alternative to Calibre (we'll call it 'calibre-web' from here down,
noting that ``calibreweb_*`` variables do not include the dash, per Ansible
recommendations).

Using It
--------

After installation, try out calibre-web at http://box/books (or box.lan/books).

Typically students access it without a password (to read and download books)
whereas teachers add books using an administrative account, as follows::

  Username: Admin
  Password: changeme

If the default configuration is not found, calibre-web server creates a
new settings file with calibre-web's own administrative account default::

  Username: admin
  Password: admin123

Backend
-------

You can manage the backend calibre-web server with these systemd commands::

  systemctl enable calibre-web
  systemctl restart calibre-web
  systemctl status calibre-web
  systemctl stop calibre-web

Configuration
-------------

To configure calibre-web, login as user 'Admin' then click 'Admin' on top.
Check 'Configuration' options near the bottom of the page.

Critical settings are stored in::

  /library/calibre-web/config/app.db

Your e-book metadata is stored in a Calibre-style database::

  /library/calibre-web/metadata.db

See also::

  /library/calibre-web/metadata_db_prefs_backup.json

Back Up Your Content
--------------------

Please back up the entire folder ``/library/calibre-web`` before upgrading —
as it contains your calibre-web content **and** settings!

Upgrading
---------

Reinstalling calibre-web automatically upgrades to the latest version.

Back up your content **and** settings before reinstalling, as explained above.

**Move your /library/calibre-web/metadata.db if you're sure you want to install
a bare/minimal metadata.db and force all settings to the default.  Then run**::

  cd /opt/iiab/iiab
  ./runrole calibre-web
  
Or, to reinstall all of Internet-in-a-Box::

  cd /opt/iiab/iiab
  ./iiab-install --reinstall

Or, if you just want to upgrade calibre-web code alone, prior to proceeding
manually::

  cd /opt/iiab/calibre-web
  git pull

Known Issues
------------

* Trying to access an empty public bookshelf causes a system error.

* As of August 2018, calibre-web doesn't yet include Calibre's e-book
  conversion functionality (e.g. Calibre 3.27.1 [released 2018-07-06] allows
  teachers to convert between PDF, epub, txt etc — to permit reading on a wider
  array client devices and client software).

* calibre-web does not currently use version numbers, so glitches might
  occasionally arise using its master branch.  Please assist us in reporting
  issues here, if they do arise: https://github.com/janeczku/calibre-web/issues
