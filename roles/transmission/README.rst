=====================
Transmission README
=====================
Transmission is a set of lightweight BitTorrent clients (in GUI, CLI and daemon form). All its incarnations feature a very simple, intuitive
 interface on top on an efficient, cross-platform back-end.

In Internet in a box we are using transmission-daemon, transmission-cli and transmission-remote-cli.

#transmission-cli - lightweight BitTorrent client (command line programs)
#transmission-daemon - lightweight BitTorrent client (daemon)
#transmission-remote-cli - ncurses interface for the Transmission BitTorrent daemon

 Access
 ------

You can access transmission using http://box/port or using the command line program.


 Adding torrents
 ---------------

The torrents are added by provisioning system based on the variables. You can also add
your own torrent using web UI or command-line option. 

$ transmission-remote-cli http://pantry.learningequality.org/downloads/ka-lite/0.17/content/ \
ka-lite-0.17-resized-videos-english.torrent




 Troubleshooting
 ----------------
