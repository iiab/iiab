===================
Transmission README
===================

Transmission is a set of lightweight BitTorrent clients (in GUI, CLI and daemon form).  All these incarnations feature a very simple and intuitive interface, on top on an efficient, cross-platform back-end.

Transmission is intended to download KA Lite content to IIAB, from places like http://pantry.learningequality.org/downloads/ka-lite/0.17/content/ -- and also to seed it, in assistance of others.

Once the packages are downloaded, please verify the content before copying it (carefully) to KA Lite content directory: /library/ka-lite/content

Caution
-------

Usage of Transmission consumes significant Internet data and system resources.
Caveat emptor!  (That's Latin for "Buyer Beware")

Access
------

Login to Transmission's web interface http://box:9091 using administrative account:

Username: Admin
Password: changeme

Alternatively, you can type 'transmission-remote' at the command-line.

Configuration
-------------

You can configure Transmission using its web interface http://box:9091

You can also edit Transmission settings in '/etc/transmission-daemon/settings.json'.  Before you start editing the
'settings.json' file, please ensure that transmission-daemon.service is stopped:

$ sudo systemctl stop transmission-daemon.service

$ sudo nano /etc/transmission-daemon/settings.json

Adding torrents
---------------

Transmission can facilitate provisioning your IIAB, by adding KA Lite content from places like: http://pantry.learningequality.org/downloads/ka-lite/0.17/content/

You can also download other torrents using Transmission's web interface, or by typing 'transmission-remote' at the command-line.

$ transmission-remote -a <path_to_the.torrent>

Known Issues
------------

* Default Transmission user/group (See https://github.com/transmission/transmission/issues/537).  Currently you need to set these "transmission_user" and "transmission_group" variables.  Check their values in transmission-daemon's systemd unit file: lib/systemd/system/transmission-daemon.service

* Random Ports: Currently it is not possible to use random ports in the range 49152-65535.  It is difficult to open multiple ports in IIAB's iptables-based firewall.

Troubleshooting
---------------

Please check if the transmission daemon is running:

$ sudo systemctl status transmission-daemon.service

Check that Transmission's settings are correct in: /etc/transmission-daemon/settings.json
