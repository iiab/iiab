===============
Minetest README
===============

For the first release the minetest server can only be installed in a Raspberry Pi.

To connect to the server, you will first need to download Minetest client software for each of your client devices, e.g. from: https://www.minetest.net/downloads/

The port is nominally the standard 30000 but can be changed using the variable ``minetest_port`` and
the admin user is the usual ``Admin``.  Note that no password is required.

Please note that the initial configuration is for creative mode and there are a number of mods installed. (see the list in `tasks/main.yml <tasks/main.yml>`_)

Locations on the Raspberry Pi
-----------------------------

- The config file is ``/etc/minetest/minetest.conf``
- The rest of the files are a normal layout based in ``/library/games/minetest``
