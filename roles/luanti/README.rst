=============
Luanti README
=============

`Luanti <https://www.luanti.org/>`_ (formerly Minetest) is a `Minecraft <https://en.wikipedia.org/wiki/Minecraft>`_-inspired creative/explorational building blocks game, written from scratch and licensed
under LGPL 2.1+.

The Luanti multiplayer server can be installed as part of any Internet-in-a-Box (IIAB) — examples of Luanti in education: `luanti.org/education <https://www.luanti.org/education/>`_

It supports both survival and creative modes along with multiplayer support, dynamic lighting, and an "infinite" map generator.  Initial configuration is "creative mode" by default, and a number of mods are installed (see the list in `tasks/install.yml <tasks/install.yml>`_).

Install Luanti onto each Student Device
---------------------------------------

Before students can connect, Luanti client software needs to be downloaded and installed onto their individual devices.

1. If a student device is Android, Windows or Mac, install it using: `luanti.org/downloads <https://www.luanti.org/downloads/>`_

2. Or, if a student device is Raspberry Pi OS or any other Linux, `install Flatpak <https://flathub.org/setup>`_ and then,

   - Install Luanti::

      flatpak install flathub net.minetest.Minetest

   - Run Luanti::

      flatpak run net.minetest.Minetest

Finally, any student can now connect to the multiplayer game: (if Luanti server is running on the IIAB!)

- Click **Join Game**.
- In the **Address** field, type in IIAB's IP address (e.g. 10.10.10.10, or box.lan).
- Click **Register** to create a student account (password optional!)
- After **Login**, help students understand Luanti's `keyboard controls <https://docs.luanti.org/for-players/getting-started/#basic-controls>`_.

*[ SCREENSHOT(S) & GAME TIPS FOR EDUCATORS FORTHCOMING ]*

.. The port is nominally the standard 30000.  If necessary, change ``luanti_port`` on the server side (IIAB side) as explained below.

.. The admin user is the usual: Admin

.. No password is required.

Optional Server-side Customizations
-----------------------------------

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
- Monitor Ubuntu 25.10 and 26.04 to see how they refine ``/usr/lib/systemd/system/minetest-server.service`` (or luanti-server.service) in 2025 and 2026 — perhaps softcoding ``--gameid minetest_game`` on the ``ExecStart=`` line, as they rename apt package 'minetest-server' to 'luanti-server' — as Debian 13 has already done? (`#3985 <https://github.com/iiab/iiab/pull/3985#issuecomment-2791734459>`_)
