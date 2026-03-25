==============
KA Lite README
==============

This role installs KA Lite, an offline version of Khan Academy (https://www.khanacademy.org) created by Learning Equality
(https://learningequality.org/ka-lite/).

KA Lite downloads Khan Academy videos to your Internet-in-a-Box for offline use, with exercises and accounts if students want to track their own progress.

[Originally KA Lite had two servers, a light httpd server that served Khan Academy videos, and a cron server that set up cron jobs to download language packs and KA videos from the internet.  There were separate flags to enable these two servers.]

Using It
--------

If enabled with the default settings, KA Lite should be accessible at http://box:8008 or http://box.lan:8008

After your Internet-in-a-Box (IIAB) is completely installed, log in to KA Lite to explore and configure::

  Username: Admin
  Password: changeme

Bulk Downloading Videos
-----------------------

Videos and their corresponding PNG thumbnail images can be copied into /library/ka-lite/content — then log in to http://box.lan:8008 and click the "Videos" tab -> "Scan content folder for videos" (which might take a few minutes to complete!)

Please see http://FAQ.IIAB.IO ("KA Lite Administration: What tips & tricks exist?") to use BitTorrent to download compressed KA Lite videos, that are much smaller than the ones downloaded via KA Lite's administrative interface.

As of August 2018, please also consider the `"Transmission" BitTorrent tool <https://github.com/iiab/iiab/tree/master/roles/transmission#transmission-readme>`_ that will automatically download thousands of KA Lite videos to your Internet-in-a-Box (IIAB) — if you install and enable "transmission" within /etc/iiab/local_vars.yml — carefully choosing the language(s) you want as downloading these videos can take many hours if not days!

Configuration Parameters
------------------------

Look at `role/kalite/defaults/main.yml <https://github.com/iiab/iiab/blob/master/roles/kalite/defaults/main.yml>`_ for the default values of the various install parameters.

Troubleshooting
---------------

*In late 2017, Internet-in-a-Box added a virtual environment (/usr/local/kalite/venv/) to keep KA Lite's Python package/dependency risks under control.  As such the command* `/usr/bin/kalite <https://github.com/iiab/iiab/blob/master/roles/kalite/templates/kalite.sh.j2>`_ *is a wrapper to this virtualenv*.  **Consequently, the following steps are no longer needed:**

Starting with KA Lite 0.15 (October 2015) you could run the server manually with the following commands:

* systemctl stop kalite-serve (make sure the systemd service is not running)
* export KALITE_HOME=/library/ka-lite (point kalite to the right environment)
* kalite start (start the server; took several minutes on older environments)

To return to using the systemd unit:

* export KALITE_HOME=/library/ka-lite (point kalite to the right environment)
* kalite stop
* systemctl start kalite-serve

More Tips & Tricks
------------------

If you're online, please see "KA Lite Administration: What tips & tricks exist?" at: http://FAQ.IIAB.IO

If you're offline, Internet-in-a-Box's FAQ (Frequently Asked Questions) is here: http://box/info
