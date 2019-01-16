================
Mosquitto README
================

Adds the `Mosquitto <https://mosquitto.org/>`_ (`MQTT <https://mqtt.org/faq>`_) `pub-sub <https://en.wikipedia.org/wiki/Publish–subscribe_pattern>`_ broker to Internet-in-a-Box (IIAB) for educational experiments with  `IoT <https://en.wikipedia.org/wiki/Internet_of_things>`_.

Roughly follows this guide: https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-the-mosquitto-mqtt-messaging-broker-on-ubuntu-16-04

Using It
-------

The Mosquitto service is authenticated with:

Username: ``Admin``

Password: ``changeme``

You can monitor it with command::

  systemctl status mosquitto

See Also
--------

`Node-RED <../nodered/README.rst>`_
