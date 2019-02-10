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

After installing Node-RED as part IIAB, please log in to http://box:1880 or http://box.lan/nodered with:

Username: ``Admin``

Password: ``changeme``

You can monitor the Node-RED service with command::

  systemctl status node-red

See Also
--------

`Mosquitto (MQTT) <../mosquitto/README.rst>`_
