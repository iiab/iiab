===============
Minetest README
===============

For the first release the minetest server can only be installed in a Raspberry Pi.

You will need a minetest client app for your device in order to connect to the server.

The port is nominally the standard 30000 but can be changed using the variable minetest_port and
the admin user is the usual Admin. Note that no password is required.

Please note that the initial configuration is for creative mode and there are a number of mods installed.
(see the list in tasks/main.yml)

Locations on the Raspberry Pi
-----------------------------

- The config file is /etc/minetest/minetest.conf
- The rest of the files are a normal layout based in /library/games/minetest
