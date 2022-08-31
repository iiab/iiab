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

Transmission is intended to download KA Lite content to Internet-in-a-Box (IIAB) from places like https://pantry.learningequality.org/downloads/ka-lite/0.17/content/ — and also to seed content, assisting others.

For example, once KA Lite videos and thumbnails are confirmed downloaded, copy them (carefully!) from ``/library/transmission`` into ``/library/ka-lite/content`` as outlined by "KA Lite Administration: What tips & tricks exist?" at http://FAQ.IIAB.IO

Caution
-------

Usage of Transmission consumes significant Internet data and system resources.
Caveat emptor!  (That's Latin for "Buyer Beware")

Using It
--------

Install Transmission by setting 'transmission_install' and 'transmission_enabled' to True in `/etc/iiab/local_vars.yml <https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it%3F>`_ — carefully choosing language(s) for KA Lite videos you want to download — and then install IIAB.  Or, if IIAB is already installed, run as root::

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

These are further explained in https://github.com/transmission/transmission/wiki/Configuration-Files (to align with the above, apt package transmission-daemon sets user debian-transmission's home directory to ``/var/lib/transmission-daemon`` in /etc/passwd).

Logging
-------

To turn on logging and/or record the Process ID (PID), follow these instructions: https://pawelrychlicki.pl/Home/Details/59/transmission-daemon-doesnt-create-a-log-file-nor-a-pid-file-ubuntu-server-1804

This gives permissions to user ``debian-transmission`` — if you use these 3 lines in ``/lib/systemd/system/transmission-daemon.service`` :

::

  RuntimeDirectory=transmission-daemon
  LogsDirectory=transmission-daemon
  ExecStart=/usr/bin/transmission-daemon -f --log-error --log-debug --logfile /var/log/transmission-daemon/transmission.log --pid-file /run/transmission-daemon/transmission.pid

Noting that one should not normally edit files in ``/lib`` or ``/usr/lib`` — systemd has a command for customizing unit files: ``systemctl edit --full transmission-daemon.service``
