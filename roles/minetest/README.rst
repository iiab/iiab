===============
Minetest README
===============

For the first release, the Minetest server can only be installed on a Raspberry Pi.

Please note that the initial configuration is for creative mode, and a number of mods are installed (see the list in `tasks/main.yml <tasks/main.yml>`_).

Connecting to the Server
------------------------

To connect to the server, you will also need to download Minetest client software for each of your client devices, e.g. from: https://www.minetest.net/downloads/

The port is nominally the standard 30000.  This can be changed in `/etc/iiab/local_vars.yml <http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F>`_ using variable: ``minetest_port``

The admin user is the usual: ``Admin``

No password is required.

File Locations on Raspberry Pi
------------------------------

- The config file is: ``/etc/minetest/minetest.conf``
- The rest of the files are a normal layout based in: ``/library/games/minetest``
