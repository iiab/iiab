===============
Minetest README
===============

`Minetest <https://www.minetest.net/>`_ is a `Minecraft <https://en.wikipedia.org/wiki/Minecraft>`_-inspired creative/explorational building blocks game, written from scratch and licensed
under the LGPL (version 2.1 or later).  It supports both survival and creative modes along with multiplayer support, dynamic lighting, and an "infinite" map generator.

The Minetest multiplayer server can be installed as part of Internet-in-a-Box (IIAB) on Raspberry Pi (Raspbian), Ubuntu 18.04 and Debian 9 Stretch.

Please note that the initial configuration is for creative mode, and a number of mods are installed (see the list in `tasks/main.yml <tasks/main.yml>`_).

Connecting to the Server
------------------------

To connect to the server, you will also need to download Minetest client software for each of your client devices, e.g. from: https://www.minetest.net/downloads/

The port is nominally the standard 30000.  If necessary, change the ``minetest_port`` as explained below.

The admin user is the usual: ``Admin``

No password is required.

Configurable Parameters
-----------------------

If changes are necessary, please edit `/etc/iiab/local_vars.yml <https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it%3F>`_ (adding any variables that you need) prior to installation if possible:

- ``minetest_install:`` set Minetest up to install; default is False
- ``minetest_enabled:`` set Minetest up to be enabled; default is False
- ``minetest_port:`` port on which client should connect; default is 30000
- ``minetest_server_admin:`` user with all permissions on minetest server; default is Admin

- ``minetest_default_game:`` only carbone-ng and minetest are supported; default is `carbone-ng <https://github.com/Calinou/carbone-ng>`_
- ``minetest_flat_world:`` use a flat mapgen engine to lower computation on client; default is False

After installation, you can monitor the 'minetest-server' service with command::

  systemctl status minetest-server

File Locations
--------------

- The config file is ``/etc/minetest/minetest.conf``
- The world files are at ``/library/games/minetest/worlds/world``

File Locations on Raspberry Pi
------------------------------

- The server binary is ``/library/games/minetest/bin/minetestserver``
- The working directory is ``/library/games/minetest``
- mods are in  ``/library/games/minetest/games/<game>/mods``

File Locations on Other Platforms
---------------------------------

- The server binary is ``/usr/lib/minetest/minetestserver``
- The working directory is ``/usr/share/games/minetest``
- mods are in  ``/usr/share/games/minetest/games/<game>/mods``

To Do
-----

- Add more mods — currently only the default mods are there in carbone-ng
- Add more games
- Minetest client software for Windows and Android, included onboard IIAB for offline communities (`#1465 <https://github.com/iiab/iiab/issues/1465>`_)
