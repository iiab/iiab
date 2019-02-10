===============
Minetest README
===============

Minetest is an open source clone of `Minecraft <https://en.wikipedia.org/wiki/Minecraft>`_, the creative/explorational building blocks game.

For the first release, the Minetest server can only be installed on a Raspberry Pi.

Please note that the initial configuration is for creative mode, and a number of mods are installed (see the list in `tasks/main.yml <tasks/main.yml>`_).

Connecting to the Server
------------------------

To connect to the server, you will also need to download Minetest client software for each of your client devices, e.g. from: https://www.minetest.net/downloads/

The port is nominally the standard 30000.  This can be changed in `/etc/iiab/local_vars.yml <http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F>`_ using variable: ``minetest_port``

The admin user is the usual: ``Admin``

No password is required.

Configurable Parameters
-----------------------

- minetest_install: set minetest up to install; default is False
- minetest_enabled: set minetest up to be enabled; default is False
- minetest_port: port on which client should connect; default is 30000
- minetest_server_admin: user with all permissions on minetest server; default is Admin

- minetest_default_game: only carbone-ng and minetest are supported; default is carbone-ng
- minetest_flat_world: use a flat mapgen engine to lower computation on client; default is False

File Locations
--------------
- The config file is: ``/etc/minetest/minetest.conf``
- The world files are at ``/library/games/minetest/worlds/world``

File Locations on Raspberry Pi
------------------------------
- The server binary is ``/library/games/minetest/bin/minetestserver``
- The working directory is ``//library/games/minetest``
- mods are in  ``/library/games/minetest/games/<game>/mods``

File Locations on Other Platforms
---------------------------------
- The server binary is ``/usr/lib/minetest/minetestserver``
- The working directory is ``/usr/share/games/minetest``
- mods are in  ``/usr/share/games/minetest/games/<game>/mods

To Do
-----
- Add more mods - currently only the default mods are there in carbone-ng
- Add more games
