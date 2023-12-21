================
Mosquitto README
================

Adds the `Mosquitto <https://mosquitto.org/>`_ (`MQTT <https://mqtt.org/faq>`_) `pub-sub <https://en.wikipedia.org/wiki/Publish–subscribe_pattern>`_ broker to Internet-in-a-Box (IIAB) for electronics projects and educational experiments with  `IoT <https://en.wikipedia.org/wiki/Internet_of_things>`_.

Roughly follows this guide: https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-the-mosquitto-mqtt-messaging-broker-on-ubuntu-16-04

Using It
--------

Prior to installing IIAB, make sure your `/etc/iiab/local_vars.yml <https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it%3F>`_ contains::

  mosquitto_install: True
  mosquitto_enabled: True

The Mosquitto service is authenticated with:

Username: ``Admin``

Password: ``changeme``

You can monitor it with command::

  systemctl status mosquitto

See Also
--------

`Node-RED <../nodered#node-red-readme>`_
