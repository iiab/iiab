=====================
Transmission README
=====================
Transmission is a set of lightweight BitTorrent clients (in GUI, CLI and daemon form). All its incarnations feature a very simple, intuitive
 interface on top on an efficient, cross-platform back-end.

The transmission program is used to download and seed Ka-Lite packages. Once the packages are downloaded, Please verify the content
before copying them to Ka-Lite content directory.

Caution
-------
Usage of transmission consumes significant Internet data and system resources.
Caveat emptor! (That's Latin for "Buyer Beware").

 Access
 ------

You can login transmission using its web interface http://box:9091/ with the following administration account.

Username: Admin
Password: changeme

Alternatively you can also access transmission using the 'transmission-remote' or 'transmission-remote' on the command line.

Configuration
--------------
You can configure transmission using the web interface http://box:9091.

You can also edit the transmission settings in '/etc/transmission-daemon/settings.json'. Before you start editing the
'settings.json' file,  Please ensure that transmission-daemon.service is stop.

$ sudo systemctl stop transmission-daemon.service
$ sudo nano /etc/transmission-daemon/settings.json


 Adding torrents
 ---------------
The transmission provisioning system is designed to add ka-Lite packages. You can also use transmission is
download torrent using the Transmission web interface or using 'transmission-remote' program.

$ transmission-remote -a <path_to_the.torrent>

Known Issues
-------------
Currently it is not possible to use random ports in the range 65535-49152. It is difficult to open multiple ports in IIAB firewall.


 Troubleshooting
 ----------------

Please check if the transmission daemon is running:

$ sudo systemctl status transmission-daemon.service

Check the transmission settings '/etc/transmission-daemon/settings.json' are correct.
