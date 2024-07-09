.. |ss| raw:: html

   <strike>

.. |se| raw:: html

   </strike>

.. |nbsp| unicode:: 0xA0
   :trim:

===================
Transmission README
===================

Transmission is a set of lightweight BitTorrent clients (in GUI, CLI and daemon form).  All these incarnations feature a very simple and intuitive interface, on top on an efficient, cross-platform backend: https://transmissionbt.com

Transmission is intended to download content like KA Lite to Internet-in-a-Box (IIAB), from places like https://pantry.learningequality.org/downloads/ka-lite/0.17/content/ — and also to seed content, assisting others.

For example, once KA Lite videos and thumbnails are confirmed downloaded, copy them (carefully!) from ``/library/transmission`` into ``/library/ka-lite/content`` as outlined by "KA Lite Administration: What tips & tricks exist?" at http://FAQ.IIAB.IO

Transmission 4.x Preview (Optional)
-----------------------------------

2023-12-31: To make the `latest Transmission features <https://github.com/transmission/transmission/commits/main>`_ available to you, Internet-in-a-Box can compile the very latest (above and beyond `Transmission 4.x+ official releases <https://github.com/transmission/transmission/releases>`_).   Just note this can take most of an hour, and is not without risk!

If you decide you want this, set ``transmission_compile_latest: True`` in `/etc/iiab/local_vars.yml <https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it%3F>`_ prior to installing Transmission, as explained below.

NOTE: Later in 2024, fast auto-installation of `Transmission 4.1+ <https://github.com/transmission/transmission/milestones>`_ should once again hopefully become mainline (`#5585 <https://github.com/transmission/transmission/discussions/5585>`_, `PR #5866 <https://github.com/transmission/transmission/pull/5866>`_) just as in recent years with Transmission 3.0 (originally from May, 2020).

.. Transmission can consume significant Internet data and system resources.  Caveat emptor!  (That's Latin for "Buyer Beware")

Using It
--------

Install Transmission by setting ``transmission_install: True`` and ``transmission_enabled: True`` in `/etc/iiab/local_vars.yml <https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it%3F>`_ — carefully choosing language(s) for KA Lite videos you want to download — and then install IIAB.  Or, if IIAB is already installed, run as root::

  cd /opt/iiab/iiab
  ./runrole transmission
  
Log in to Transmission's web interface http://box:9091 using administrative account::

  Username: Admin
  Password: changeme

Change the above password by editing ``rpc-password`` in ``/etc/transmission-daemon/settings.json`` (your plaintext will be hashed to conceal it, the next time Transmission is started).

Finally if you prefer the command-line, you can instead run `transmission-remote <https://linux.die.net/man/1/transmission-remote>`_ commands.

Configuration
-------------

Configure Transmission using its web interface: http://box:9091

More settings can be changed within `/etc/transmission-daemon/settings.json <https://github.com/holta/iiab/blob/transmission-settings/roles/transmission/templates/settings.json.j2>`_ if you first ensure that the transmission-daemon.service is stopped::

  systemctl stop transmission-daemon

Then edit the file::

  nano /etc/transmission-daemon/settings.json

Here are some short explanations, as to what those ~68 variables mean: https://github.com/transmission/transmission/wiki/Editing-Configuration-Files

After saving your changes in 'settings.json', restart Transmission by running::

  systemctl restart transmission-daemon

*2021-03-14: Transmission 2.94 and 3.00 were intermittently* **ignoring** */etc/transmission-daemon/settings.json (presumably when the file was deemed problematic/missing/etc) and creating their own* ``/var/lib/transmission-daemon/.config/transmission-daemon/settings.json`` *(i.e. suddenly a FILE instead of transmission-deamon's out-of-the-box SYMLINK to /etc/transmission-daemon/settings.json).  IIAB* `PR #2707 <https://github.com/iiab/iiab/pull/2707>`_ *should fix this problem, by reversing the direction of the symlink created by apt.  See* `Troubleshooting <./README.rst#Troubleshooting>`_ *below.*

Adding Torrents
---------------

Transmission can facilitate provisioning content onto your IIAB, e.g. by adding thousands of KA Lite videos from places like: https://pantry.learningequality.org/downloads/ka-lite/0.17/content/

Please read the lettered instructions (A, B, C, D) in `/etc/iiab/local_vars.yml <https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it%3F>`_ and 'KA Lite Administration: What tips & tricks exist?' at http://FAQ.IIAB.IO outlining how to use Transmission to download and then install KA Lite content.

You can also download other torrents using Transmission's web interface, or by typing `transmission-remote <https://linux.die.net/man/1/transmission-remote>`_ at the command-line::

  transmission-remote -n Admin:changeme -a <URL-or-local-path.torrent>

Known Issues
------------

* |ss| Default Transmission user/group may need fixing (https://github.com/transmission/transmission/issues/537) in some circumstances.  You can set Ansible variables 'transmission_user' and 'transmission_group' e.g. in /opt/iiab/iiab/roles/transmission/defaults/main.yml (you might need 'User=' and 'Group=' in systemd unit file /lib/systemd/system/transmission-daemon.service — e.g. both might need to be set to 'debian-transmission' — if so then run 'systemctl daemon-reload' and 'systemctl restart transmission-daemon'). |se| |nbsp| `PR #2703 <https://github.com/iiab/iiab/pull/2703>`_

* Random Ports: Currently it is not possible to use random ports in the range 49152-65535, as it's difficult to open multiple ports in IIAB's `iptables-based firewall <https://github.com/iiab/iiab/wiki/IIAB-Networking#firewall-iptables>`_.

* transmission-daemon (4.0.6 or 4.1-dev) install onto Ubuntu 24.04 or 24.10, but (1) its systemd service times out (fails to start) (2) rebooting kinda helps, but service then crashes on 1st visit to http://box:9091 `#3756 <https://github.com/iiab/iiab/issues/3756>`_

Troubleshooting
---------------

Verify that transmission-daemon is running::

  systemctl status transmission-daemon

Re-check that Transmission's settings are correct here: (by following the instructions above, under `Configuration <./README.rst#Configuration>`_)

::

  /etc/transmission-daemon/settings.json

More advanced configuration and status are in directory ``/var/lib/transmission-daemon/info/`` (symlinked to /var/lib/transmission-daemon/.config/transmission-daemon/) here::

  blocklists/
  dht.dat
  resume/
  settings.json <- /etc/transmission-daemon/settings.json (PR #2707 CREATES THIS SYMLINK!)
  stats.json
  torrents/

These are further explained in |ss| https://github.com/transmission/transmission/wiki/Configuration-Files |se| (to align with the above, apt package transmission-daemon sets user debian-transmission's home directory to ``/var/lib/transmission-daemon`` in /etc/passwd).

Docs
----

As of June 2023, these docs appear to be the most up-to-date:

- https://github.com/transmission/transmission/tree/main/docs
   - https://github.com/transmission/transmission/blob/main/docs/Building-Transmission.md
   - https://github.com/transmission/transmission/blob/main/docs/Configuration-Files.md
   - https://github.com/transmission/transmission/blob/main/docs/Editing-Configuration-Files.md
   - https://github.com/transmission/transmission/blob/main/docs/Headless-Usage.md
   - https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md
      - https://transmission-rpc.readthedocs.io
- https://cli-ck.io/transmission-cli-user-guide/ (2016 but still useful)
   - https://github.com/transmission/transmission#command-line-interface-notes ("``transmission-cli`` is deprecated and exists primarily to support older hardware dependent upon it. In almost all instances, ``transmission-remote`` should be used instead.")
- https://wiki.archlinux.org/title/transmission (updated regularly)
- https://trac.transmissionbt.com/wiki (2006-2019)

Logging
-------

Increase logging by changing transmission-daemon's ``--log-level=error`` to ``--log-level=debug`` in ``/lib/systemd/system/transmission-daemon.service``

(Options are: ``critical``, ``error``, ``warn``, ``info``, ``debug`` or ``trace``)

Then run::

  systemctl daemon-reload
  systemctl restart transmission-daemon
  journalctl -eu transmission-daemon

Noting that one should not normally edit files in ``/lib`` or ``/usr/lib`` — systemd has a command for customizing unit files: ``systemctl edit --full transmission-daemon.service``
