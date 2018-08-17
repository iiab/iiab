=====================
Transmission README
=====================
Transmission is a set of lightweight BitTorrent clients (in GUI, CLI and daemon form). All its incarnations feature a very simple, intuitive
 interface on top on an efficient, cross-platform back-end.

Caution
-------
Usage of transmission consumes significant Internet data and system resources.
Caveat emptor! (That's Latin for "Buyer Beware").

 Access
 ------

You can login transmission using http://box:9091/ or using the command line program.

Username: Admin
Password: changeme

 Adding torrents
 ---------------

The torrents are added by provisioning system based on the variables. You can also add
your own torrent using web UI or command-line option.
s
$ transmission-remote -a <path_to_the.torrent>

Known Issues
-------------
Currently it is not possible to use random ports in the range 65535-49152. It is difficult to open multiple ports in IIAB firewall.



 Troubleshooting
 ----------------
