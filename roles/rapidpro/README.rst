==============
RapidPro README
==============

This Ansible role installs `RapidPro <https://rapidpro.io/>`_ within `Internet-in-a-Box (IIAB) <https://internet-in-a-box.org/>`_. RapidPro is an open-source platform that allows you to visually build interactive messaging applications.

Using It
--------

If enabled and with the default settings, RapidPro should be accessible at: http://box/rp

Log in to RapidPro with::

  Username: admin@box.lan
  Password: changeme

Configuration Parameters
------------------------

Please look in `/opt/iiab/iiab/roles/rapidpro/defaults/main.yml <defaults/main.yml>`_ for the default values of the various install parameters.  Everything in this README assumes the default values.

To enable the role, add the following to `/etc/iiab/local_vars.yml <http://faq.iiab.io/What_is_local_vars.yml_and_how_do_I_customize_it%3F>`_::

  rapidpro_install: true

To disable the services while still having the role installed, add the following to `/etc/iiab/local_vars.yml`::

  rapidpro_enabled: false

*Feel free to override any of the above, by copying the relevant line from /opt/iiab/iiab/roles/rapidpro/defaults/main.yml to /etc/iiab/local_vars.yml (then run* ``cd /opt/iiab/iiab`` *followed by* ``./runrole rapidpro`` *per IIAB's general guidelines at http://FAQ.IIAB.IO).*

Troubleshooting
---------------

If you encounter issues, you can check the logs for the gunicorn and nginx services:

.. code-block:: bash

  sudo journalctl -u rapidpro-gunicorn
  sudo journalctl -u nginx

You can also try restarting the services:

.. code-block:: bash

  sudo systemctl restart rapidpro-gunicorn
  sudo systemctl restart nginx

Known Issues
------------

* There are no known issues at this time.