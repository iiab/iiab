===================
Transmission README
===================

Transmission is a set of lightweight BitTorrent clients (in GUI, CLI and daemon form).  All these incarnations feature a very simple and intuitive interface, on top on an efficient, cross-platform backend.

Transmission is intended to download KA Lite content to IIAB, from places like http://pantry.learningequality.org/downloads/ka-lite/0.17/content/ — and also to seed content, assisting others.

Once the packages are downloaded, please verify the content before copying it (carefully!) into KA Lite content directory: ``/library/ka-lite/content``

Caution
-------

Usage of Transmission consumes significant Internet data and system resources.
Caveat emptor!  (That's Latin for "Buyer Beware")

Using It
--------

Login to Transmission's web interface http://box:9091 using administrative account::

  Username: Admin
  Password: changeme

Alternatively, you can run ``transmission-remote`` at the command-line.

Configuration
-------------

Configure Transmission using its web interface: http://box:9091

You can also edit Transmission settings in '/etc/transmission-daemon/settings.json'.  Before you edit this file, ensure that transmission-daemon.service is stopped::

  systemctl stop transmission-daemon
  nano /etc/transmission-daemon/settings.json

Adding torrents
---------------

Transmission can facilitate provisioning content onto your IIAB, e.g. by adding KA Lite content from places like: http://pantry.learningequality.org/downloads/ka-lite/0.17/content/

You can also download other torrents using Transmission's web interface, or by typing 'transmission-remote' at the command-line::

  transmission-remote -a <path_to_the.torrent>

Known Issues
------------

* Default Transmission user/group may need fixing (https://github.com/transmission/transmission/issues/537).  You can set Ansible variables 'transmission_user' and 'transmission_group' e.g. in /opt/iiab/iiab/roles/transmission/defaults/main.yml (in the end check 'User=' and 'Group=' in systemd unit file /lib/systemd/system/transmission-daemon.service — both might need to be set to 'debian-transmission' — followed by 'systemctl daemon-reload' then 'systemctl restart transmission-daemon').

* Random Ports: Currently it is not possible to use random ports in the range 49152-65535.  It is difficult to open multiple ports in IIAB's iptables-based firewall.

Troubleshooting
---------------

Verify that transmission-daemon is running::

  systemctl status transmission-daemon

Check that Transmission's settings are correct in::

  /etc/transmission-daemon/settings.json
