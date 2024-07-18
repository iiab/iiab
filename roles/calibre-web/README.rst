.. |ss| raw:: html

   <strike>

.. |se| raw:: html

   </strike>

.. |nbsp| unicode:: 0xA0
   :trim:

==================
Calibre-Web README
==================

This Ansible role installs
`Calibre-Web <https://github.com/janeczku/calibre-web#readme>`_ as a modern
client-server alternative to Calibre, for your
`Internet-in-a-Box (IIAB) <https://internet-in-a-box.org>`_.

Calibre-Web provides a clean web interface for students to browse, read and
download e-books using a
`Calibre-compatible database <https://manual.calibre-ebook.com/db_api.html>`_.

Teachers upload e-books, adjust e-book metadata, and create custom "bookshelf"
collections — to help students build the best local community library!

**NEW AS OF JANUARY 2024:** `IIAB's experimental new version of Calibre-Web <https://github.com/iiab/calibre-web/wiki>`_
**also lets you add YouTube and Vimeo videos (and local videos, e.g. from
teachers' phones) to expand your indigenous/local/family learning library!**

.. image:: https://www.yankodesign.com/images/design_news/2019/05/221758/luo_beetle_library_8.jpg

🍒 GURU TIPS 🍒

* Calibre-Web takes advantage of Calibre's own `/usr/bin/ebook-convert
  <https://manual.calibre-ebook.com/generated/en/ebook-convert.html>`_ program
  if that's installed — so consider also installing
  `Calibre <https://calibre-ebook.com/whats-new>`_ during your IIAB
  installation — *if you tolerate the weighty ~1 GB (of graphical OS libraries)
  that Calibre mandates!*

* If you choose to also install Calibre (e.g. by running
  ``sudo apt install calibre``) then you'll get useful e-book
  importing/organizing tools like
  `/usr/bin/calibredb <https://manual.calibre-ebook.com/generated/en/calibredb.html>`_.

Install It
----------

Install Calibre-Web by setting these 2 variables in
`/etc/iiab/local_vars.yml <https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it%3F>`_::

  calibreweb_install: True
  calibreweb_enabled: True

Then install IIAB (`download.iiab.io <https://download.iiab.io>`_).  Or if
IIAB's already installed, run::

  cd /opt/iiab/iiab
  sudo ./runrole calibre-web

NOTE: Calibre-Web's Ansible role (playbook) in
`/opt/iiab/iiab/roles <https://github.com/iiab/iiab/tree/master/roles>`_ is
``calibre-web`` which contains a hyphen — *whereas its Ansible variables*
``calibreweb_*`` *do NOT contain a hyphen!*

Using It
--------

Try Calibre-Web on your own IIAB by browsing to http://box/books (or
http://box.lan/books).

*Students* access it without a password (to read and download books).

*Teachers* add and arrange books using an administrative account, by clicking
**Guest** then logging in with::

  Username: Admin
  Password: changeme

🍒 GURU TIPS 🍒

* If Calibre-Web's configuration file (app.db) goes missing, the administrative
  account will revert to::

    Username: admin
    Password: admin123

* If you lose your password, you can change it with the
  ``-s [username]:[newpassword]`` command-line option:
  https://github.com/janeczku/calibre-web/wiki/FAQ#what-do-i-do-if-i-lose-my-admin-password

Configuration
-------------

To configure Calibre-Web browse to http://box/books then click **Guest** to log
in as user **Admin** (default passwords above!)

Then click the leftmost **Admin** button to administer — considering all 3
**Configuration** buttons further below.

These critical settings are stored in::

  /library/calibre-web/config/app.db

Whereas your e-book metadata is stored in a Calibre-style database::

  /library/calibre-web/metadata.db

Videos' metadata is stored in database::

  /library/calibre-web/xklb-metadata.db

See also::

  /library/calibre-web/metadata_db_prefs_backup.json

Finally, take note of Calibre-Web's
`FAQ <https://github.com/janeczku/calibre-web/wiki/FAQ>`_ and official docs on
its
`Runtime Configuration Options <https://github.com/janeczku/calibre-web/wiki/Configuration>`_
and
`Command Line Interface <https://github.com/janeczku/calibre-web/wiki/Command-Line-Interface>`_.

Backend
-------

You can manage the backend Calibre-Web server with systemd commands like::

  systemctl status calibre-web
  systemctl stop calibre-web
  systemctl restart calibre-web

Run all commands
`as root <https://unix.stackexchange.com/questions/3063/how-do-i-run-a-command-as-the-system-administrator-root>`_.

Errors and warnings can be seen if you run::

  journalctl -u calibre-web

Log verbosity level can be
`adjusted <https://github.com/janeczku/calibre-web/wiki/Configuration#logfile-configuration>`_
within Calibre-Web's **Configuration > Basic Configuration > Logfile
Configuration**.

Finally, http://box/live/stats (Calibre-Web's **About** page) can be a very
useful list of ~42 `Calibre-Web dependencies <https://github.com/janeczku/calibre-web/wiki/Dependencies-in-Calibre-Web-Linux-and-Windows>`_
(mostly Python packages, and the version number of each that's installed).

Back Up Everything
------------------

Please back up the entire folder ``/library/calibre-web`` before upgrading —
as it contains your Calibre-Web content **and** configuration settings!

Upgrading
---------

Please see our `new/automated upgrade technique (iiab-update) <https://github.com/iiab/calibre-web/wiki#upgrading>`_
introduced in July 2024.

But first: back up your content **and** configuration settings, as outlined
above!

**Conversely if you're sure you want to fully reset your Calibre-Web settings,
and remove all existing e-book/video/media metadata — then move your
/library/calibre-web/config/app.db, /library/calibre-web/metadata.db and
/library/calibre-web/xklb-metadata.db out of the way.**

RECAP: Either way, "reinstalling" Calibre-Web automatically installs the latest
version — so long as your Internet-in-a-Box (IIAB) is online.  Most people
should stick with the new ``iiab-update`` technique above.  However if you must
use the older/manual approach, you would need to run, as root::

  cd /opt/iiab/iiab
  ./runrole --reinstall calibre-web

Or, if there's a need to try updating Calibre-Web's code alone::

  cd /usr/local/calibre-web-py3
  git pull

Finally, this much older way is *no longer recommended*::

  cd /opt/iiab/iiab
  ./iiab-install --reinstall    # OR: ./iiab-configure

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

* *Please report serious issues here:*
  https://github.com/iiab/calibre-web/issues
