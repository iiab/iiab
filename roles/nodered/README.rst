===============
Node-RED README
===============

Adds `Node-RED <https://nodered.org/>`_ and `Node-RED Dashboard <https://flows.nodered.org/node/node-red-dashboard>`_ to Internet-in-a-Box (IIAB) for electronics projects and educational experiments with `IoT <https://en.wikipedia.org/wiki/Internet_of_things>`_.

Node-RED is a flow-based development tool for visual programming developed originally by IBM for wiring together hardware devices, APIs and online services as part of the Internet of Things.  Node-RED provides a web browser-based flow editor, which can be used to create JavaScript functions.

Using It
--------

Prior to installing IIAB, make sure your `/etc/iiab/local_vars.yml <http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F>`_ contains::

  nodered_install: True
  nodered_enabled: True

After installing Node-RED as part IIAB, please log in to http://box/nodered or http://box:1880/nodered with:

Username: ``Admin``

Password: ``changeme``

To change this password, please see: `roles/nodered/defaults/main.yml <defaults/main.yml#L12-L27>`_

You can monitor the Node-RED service with command::

  systemctl status nodered

Raspberry Pi Zero W Warning
---------------------------

Node.js applications like Asterisk/FreePBX, Node-RED and Sugarizer won't work on Raspberry Pi Zero W (ARMv6) if you installed Node.js while on RPi 3, 3 B+ (ARMv7) or RPi 4 (ARMv8).  If necessary, run ``apt remove nodejs`` or ``apt purge nodejs`` then ``rm /etc/apt/sources.list.d/nodesource.list; apt update`` then (`attempt! <https://nodered.org/docs/hardware/raspberrypi#swapping-sd-cards>`_) to `install Node.js <https://github.com/iiab/iiab/blob/master/roles/nodejs/tasks/main.yml>`_ *on the Raspberry Pi Zero W itself* (a better approach than "cd /opt/iiab/iiab; ./runrole nodejs" is to try ``apt install nodejs`` or try installing the tar file mentioned at `#2082 <https://github.com/iiab/iiab/issues/2082#issuecomment-569344617>`_).  You might also need ``apt install npm``.  Whatever versions of Node.js and npm you install, make sure ``/etc/iiab/iiab_state.yml`` contains the line ``nodejs_installed: True`` (add it if nec!)  Finally, proceed to install Asterisk/FreePBX, Node-RED and/or Sugarizer.  `#1799 <https://github.com/iiab/iiab/issues/1799>`_

See Also
--------

`Mosquitto (MQTT) <../mosquitto#mosquitto-readme>`_
