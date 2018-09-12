.. |ss| raw:: html

   <strike>

.. |se| raw:: html

   </strike>

.. |nbsp| unicode:: 0xA0
   :trim:

==================
Calibre-Web README
==================

Calibre-Web provides a clean interface for browsing, reading and downloading
e-books using an existing Calibre database.  Teachers can upload e-books,
adjust e-book metadata, and create custom e-book collections ("bookshelves"):
https://github.com/janeczku/calibre-web#about

This Ansible role installs Calibre-Web as part of your Internet-in-a-Box (IIAB)
as a possible alternative to Calibre (we'll call it 'calibre-web' from here
down, noting that ``calibreweb_*`` variables do not include the dash, per
Ansible recommendations).

Using It
--------

After installation, try out calibre-web at http://box/books (or box.lan/books).

Typically students access it without a password (to read and download books)
whereas teachers add books using an administrative account, as follows::

  Username: Admin
  Password: changeme

If the default configuration is not found, the calibre-web server creates a
new settings file with calibre-web's own default administrative account::

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

To configure calibre-web, log in as user 'Admin' then click 'Admin' on top.
Check 'Configuration' options near the bottom of the page.

Critical settings are stored in::

  /library/calibre-web/config/app.db

Your e-book metadata is stored in a Calibre-style database::

  /library/calibre-web/metadata.db

See also::

  /library/calibre-web/metadata_db_prefs_backup.json

Back Up Everything
------------------

Please back up the entire folder ``/library/calibre-web`` before upgrading —
as it contains your calibre-web content **and** settings!

Upgrading
---------

Reinstalling calibre-web automatically upgrades to the latest version if your
Internet-in-a-Box (IIAB) is online.

But first: back up your content **and** settings, as explained above.

**Then move your /library/calibre-web/metadata.db out of the way, if you're
sure you want to (re)install bare/minimal metadata, and force all calibre-web
settings to the default.  Then run**::

  cd /opt/iiab/iiab
  ./runrole calibre-web
  
Or, to reinstall all of IIAB::

  cd /opt/iiab/iiab
  ./iiab-install --reinstall

Or, if you just want to upgrade calibre-web code alone, prior to proceeding
manually::

  cd /opt/iiab/calibre-web
  git pull

Known Issues
------------

* |ss| Trying to access an empty public bookshelf causes a system error. |se| |nbsp|  Appears fixed as of 2018-09-12: `janeczku/calibre-web#620 <https://github.com/janeczku/calibre-web/issues/620>`_

* |ss| As of August 2018, it's sometimes impossible to set the language of an
  e-book: `#1040 <https://github.com/iiab/iiab/issues/1040>`_, `janeczku/calibre-web#593 <https://github.com/janeczku/calibre-web/issues/593>`_ |se| |nbsp|  Appears fixed as of 2018-09-12: `janeczku/calibre-web#620 <https://github.com/janeczku/calibre-web/issues/620>`_

* |ss| As of August 2018, calibre-web doesn't yet include Calibre's e-book
  conversion functionality (e.g. Calibre 3.27.1 [released 2018-07-06] allows
  teachers to convert between PDF, EPUB, HTML, TXT etc — to permit reading on a
  wider array client devices and client software). |se| |nbsp|  This new calibre-web
  feature (which requires Calibre's ebook-converter program) is not yet quite
  working in IIAB as of 2018-09-12: `janeczku/calibre-web#624 <https://github.com/janeczku/calibre-web/issues/624>`_

* http://192.168.0.x:8083 does not work, as a result of `iptables <https://github.com/iiab/iiab/blob/master/roles/network/templates/gateway/iiab-gen-iptables#L93>`_,
  even when ``services_externally_visible: true``.  This is fixable, but perhaps
  it's not a priority, as URL's like {http://192.168.0.x/books,
  http://10.8.0.x/books, http://127.0.0.1/books and http://box/books} all work.

* calibre-web does not currently use version numbers, so glitches might
  occasionally arise, when upstream developers change its master branch without
  warning.
  
* *Please assist us in reporting serious issues here:*
  https://github.com/janeczku/calibre-web/issues
