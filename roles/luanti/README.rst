=============
Luanti README
=============

`Luanti <https://www.luanti.org/>`_ (formerly Minetest) is a `Minecraft <https://en.wikipedia.org/wiki/Minecraft>`_-inspired creative/explorational building blocks game, written from scratch and licensed
under the LGPL (version 2.1 or later).  It supports both survival and creative modes along with multiplayer support, dynamic lighting, and an "infinite" map generator.

The Luanti multiplayer server can be installed as part of any Internet-in-a-Box (IIAB).

For examples of Luanti in education, please see: `luanti.org/education <https://www.luanti.org/education/>`_

Initial configuration is "creative mode" by default, and a number of mods are installed (see the list in `tasks/install.yml <tasks/install.yml>`_).

Connecting to the Server
------------------------

To connect to the server, you will also need to download Luanti client software for each of your client devices, e.g. from: `luanti.org/downloads <https://www.luanti.org/downloads/>`_

The port is nominally the standard 30000.  If necessary, change the ``luanti_port`` as explained below.

The admin user is the usual: ``Admin``

No password is required.

Configurable Parameters
-----------------------

If changes are necessary, please edit `/etc/iiab/local_vars.yml <https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it%3F>`_ (adding any variables that you need) prior to installation:

- ``luanti_install:`` set Luanti up to install; default is False
- ``luanti_enabled:`` set Luanti up to be enabled; default is False
- ``luanti_port:`` port on which client should connect; default is 30000
- ``luanti_server_admin:`` user with all permissions on Luanti server; default is Admin
|
- ``luanti_default_game:`` only the default Luanti game is supported at present; in future the default might be DreamBuilder
- ``luanti_flat_world:`` use a flat mapgen engine to lower computation on client; default is False

After installation, you can monitor the 'luanti-server' service with command::

  systemctl status luanti-server

File Locations
--------------

- The config file is ``/etc/luanti/default.conf``
- The world files are at ``/library/games/luanti/worlds/world``
- The server is ``/usr/games/luantiserver`` with binary ``/usr/libexec/luanti/luantiserver``
- The working directory is ``/usr/share/luanti``
- mods are in ``/usr/share/luanti/games/<game>/mods``

To Do
-----

- Add more mods
- Add more games
- Luanti client software for Windows and Android, included onboard IIAB for offline communities? (`#1465 <https://github.com/iiab/iiab/issues/1465>`_)
