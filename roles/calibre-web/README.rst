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
as a possible alternative to Calibre.

*WARNING: Calibre-Web depends on Calibre's own* ``/usr/bin/ebook-convert`` *program,
so we strongly recommend you also install Calibre during your IIAB
installation!*

Please note Calibre-Web's Ansible playbook is ``/opt/iiab/iiab/roles/calibre-web``
whereas its Ansible variables ``calibreweb_*`` do **not** include the dash,
per Ansible recommendations.

Using It
--------

After installation, try out Calibre-Web at http://box/books (or box.lan/books).

Typically students access it without a password (to read and download books)
whereas teachers add books using an administrative account, as follows::

  Username: Admin
  Password: changeme

If the default configuration is not found, the Calibre-Web server creates a
new settings file with calibre-web's own default administrative account::

  Username: admin
  Password: admin123

Backend
-------

You can manage the backend Calibre-Web server with these systemd commands::

  systemctl enable calibre-web
  systemctl restart calibre-web
  systemctl status calibre-web
  systemctl stop calibre-web

Configuration
-------------

To configure Calibre-Web, log in as user 'Admin' then click 'Admin' on top.
Check 'Configuration' options near the bottom of the page.

Critical settings are stored in::

  /library/calibre-web/config/app.db

Your e-book metadata is stored in a Calibre-style database::

  /library/calibre-web/metadata.db

See also::

  /library/calibre-web/metadata_db_prefs_backup.json

See the official docs on Calibre-Web's `Runtime Configuration Options <https://github.com/janeczku/calibre-web/wiki/Configuration>`_.

Back Up Everything
------------------

Please back up the entire folder ``/library/calibre-web`` before upgrading —
as it contains your Calibre-Web content **and** settings!

Upgrading
---------

Reinstalling Calibre-Web automatically upgrades to the latest version if your
Internet-in-a-Box (IIAB) is online.

But first: back up your content **and** settings, as explained above.

**Also move your /library/calibre-web/config/app.db and
/library/calibre-web/metadata.db out of the way — if you're sure to want to
fully reset your Calibre-Web settings (to install defaults) and remove all
e-book metadata!  Then run**::

  cd /opt/iiab/iiab
  ./runrole calibre-web
  
Or, to reinstall all of IIAB::

  cd /opt/iiab/iiab
  ./iiab-install --reinstall

Or, if you just want to upgrade Calibre-Web code alone, prior to proceeding
manually::

  cd /usr/local/calibre-web-py3
  git pull

Known Issues
------------

* |ss| Trying to access an empty public bookshelf causes a system error. |se| |nbsp|  Appears fixed as of 2018-09-12: `janeczku/calibre-web#620 <https://github.com/janeczku/calibre-web/issues/620>`_

* |ss| As of August 2018, it's sometimes impossible to set the language of an
  e-book: `#1040 <https://github.com/iiab/iiab/issues/1040>`_, `janeczku/calibre-web#593 <https://github.com/janeczku/calibre-web/issues/593>`_ |se| |nbsp|  Appears fixed as of 2018-09-12: `janeczku/calibre-web#620 <https://github.com/janeczku/calibre-web/issues/620>`_

* |ss| As of August 2018, Calibre-Web doesn't yet include Calibre's e-book
  conversion functionality (e.g. Calibre 3.27.1 [released 2018-07-06] allows
  teachers to convert between PDF, EPUB, TXT etc — to permit reading on a
  wider array client devices and client software). |se| |nbsp|  Fixed by
  `janeczku/calibre-web#609 <https://github.com/janeczku/calibre-web/issues/609>`_
  in early September 2018.

* |ss| This new Calibre-Web feature (which depends on Calibre's ebook-converter 
  program) needs to be manually configured as of 2018-09-12:
  `janeczku/calibre-web#624 <https://github.com/janeczku/calibre-web/issues/624>`_
  |se| |nbsp|  Fixed by `#1127 <https://github.com/iiab/iiab/pull/1127>`_ on 2018-09-12.

  To manually enable the converting of e-books (automated above, should no
  longer be necessary!) log in to http://box/books as Admin/changeme (etc) then
  click Admin -> Basic Configuration -> External binaries.  Then change these
  2 settings:

  * Change radio button "No converter" to "Use calibre's ebook converter"
  * In textfield "Path to convertertool" type in: ``/usr/bin/ebook-convert``
  
  Then:
  
  * Submit
  * Verify that "ebook-convert" appears on Calibre-Web's "About" page at http://box/books/stats
  * Test it by clicking any e-book -> Edit metadata -> Convert book format

* |ss| http://192.168.0.x:8083 does not work, as a result of `iptables <https://github.com/iiab/iiab/blob/master/roles/network/templates/gateway/iiab-gen-iptables#L93>`_,
  even when ``services_externally_visible: true``.  This is fixable, but perhaps
  it's not a priority, as URL's like {http://192.168.0.x/books,
  http://10.8.0.x/books, http://127.0.0.1/books and http://box/books} all work. |se| |nbsp|  Marked as "wontfix" on 2018-09-12: `#1050 <https://github.com/iiab/iiab/issues/1050>`_

* |ss| Calibre-Web does not currently use version numbers, so glitches may
  occasionally arise, when upstream developers change its master branch without
  warning. |se|
  
* |ss| Imagemagick policy prevents generating thumbnails for PDF's during upload: `#1530 <https://github.com/iiab/iiab/issues/1530>`_ `janeczku/calibre-web#827 <https://github.com/janeczku/calibre-web/issues/827>`_ |se|

* |ss| Upload of not supported file formats gives no feedback to the user: `janeczku/calibre-web#828 <https://github.com/janeczku/calibre-web/issues/828>`_ |se| |nbsp|  Fixed by `361a124 <https://github.com/janeczku/calibre-web/commit/361a1243d732116e6f520fabbaae017068b86037>`_ on 2019-02-27.

* *Please assist us in reporting serious issues here:*
  https://github.com/janeczku/calibre-web/issues
