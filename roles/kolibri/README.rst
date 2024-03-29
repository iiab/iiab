==============
Kolibri README
==============

This Ansible role installs `Kolibri <https://learningequality.org/kolibri/>`_ within `Internet-in-a-Box (IIAB) <https://internet-in-a-box.org/>`_.  Kolibri is an open-source educational platform specially designed to provide offline access to a wide range of quality, openly licensed educational contents in low-resource contexts like rural schools, refugee camps, orphanages, and also in non-formal school programs.

Kolibri's online User Guide is here: `https://kolibri.readthedocs.io <https://kolibri.readthedocs.io/>`_

Using It
--------

If enabled and with the default settings, Kolibri should be accessible at: http://box/kolibri

Log in to Kolibri with::

  Username: Admin
  Password: changeme

Configuration Parameters
------------------------

Please look in `/opt/iiab/iiab/roles/kolibri/defaults/main.yml <defaults/main.yml>`_ for the default values of the various install parameters.  Everything in this README assumes the default values.

Automatic Device Provisioning
-----------------------------

When kolibri_provision is enabled (e.g. in `/etc/iiab/local_vars.yml <http://FAQ.IIAB.IO#What_is_local_vars.yml_and_how_do_I_customize_it%3F>`_) the installation will set up the following defaults::

  kolibri_facility: Kolibri-in-a-Box   
  kolibri_language: en      # See KOLIBRI_SUPPORTED_LANGUAGES at the bottom of https://github.com/learningequality/kolibri/blob/develop/kolibri/utils/i18n.py
  kolibri_preset: formal    # formal, nonformal, informal
  kolibri_admin_user: Admin
  kolibri_admin_password: changeme

*Feel free to override any of the above, by copying the relevant line from /opt/iiab/iiab/roles/kolibri/defaults/main.yml to /etc/iiab/local_vars.yml (then run* ``cd /opt/iiab/iiab`` *followed by* ``./runrole kolibri`` *per IIAB's general guidelines at http://FAQ.IIAB.IO).*

Cloning Content
---------------

Kolibri 0.10 introduced ``kolibri manage deprovision`` which will remove user configurations, leaving content intact — i.e. if student and teacher privacy requires their records be deleted.  You can then copy or clone /library/kolibri to a new location, or to a new school entirely.

Troubleshooting
---------------

This unproxied version of Kolibri can sometimes help: http://box:8009/kolibri/

If you're logged in as root (that's the general assumption of this document) you can run Kolibri manually with commands like::

  systemctl stop kolibri           # Make sure the systemd service is not running
  export KOLIBRI_HOME=/library/kolibri
  export KOLIBRI_HTTP_PORT=8009    # Otherwise Kolibri will try to run on default port 8080
  kolibri start

...while you look over Kolibri's systemd unit file (`/etc/systemd/system/kolibri.service <https://github.com/iiab/iiab/blob/master/roles/kolibri/templates/kolibri.service.j2>`_) for the latest parameters!

To return to using the systemd unit file::

  kolibri stop
  systemctl start kolibri

Known Issues
------------

* Active list of Kolibri issues, as of December 2021: `#1545 <https://github.com/iiab/iiab/issues/1545>`_

* Kolibri migrations might still take a long time on a Raspberry Pi?  These long-running migrations could cause kolibri service timeouts.  Try running migrations manually using command ``kolibri manage migrate`` after following the troubleshooting instructions above.  See: `learningequality/kolibri#4310 <https://github.com/learningequality/kolibri/issues/4310>`_

* Loading channels might still take a long time on a Raspberry Pi?  When generating channel contents for Khan Academy, the step indicated as “Generating channel listing.  This could take a few minutes…” could mean ~30 minutes.  The device’s computation power is the bottleneck.  You might get logged out while waiting, but this is harmless and the process will continue.  Sit tight!
