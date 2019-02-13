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

After installing Node-RED as part IIAB, please log in to http://box/nodered or http://box.lan:1880 with:

Username: ``Admin``

Password: ``changeme``

You can monitor the Node-RED service with command::

  systemctl status node-red

Raspberry Pi Zero W Warning
---------------------------

Node.js applications like Asterisk/FreePBX, Node-RED and Sugarizer `won't work <https://nodered.org/docs/hardware/raspberrypi#swapping-sd-cards>`_ on Raspberry Pi Zero W (ARM6) if you installed Node.js while on RPi 3 or 3 B+ (ARM7).  If necessary, run ``apt remove nodejs`` then ``cd /opt/iiab/iiab`` then `./runrole nodejs <https://github.com/iiab/iiab/blob/master/roles/nodejs/tasks/main.yml>`_ *on the Raspberry Pi Zero W itself* — before proceeding to install Asterisk/FreePBX, Node-RED and/or Sugarizer.

See Also
--------

`Mosquitto (MQTT) <../mosquitto/README.rst>`_
