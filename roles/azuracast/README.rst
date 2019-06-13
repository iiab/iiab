==========
Azuracast README
==========

This 'azuracast' playbook adds `Azuracast <https://azuracast.com/>`_ to Internet-in-a-Box (IIAB) for network radio station fnctionality.

Currently, this will only run on Ubuntu 18.04, Debian 9, Debian 10. This will not run on raspberry pi.

Using It
--------

Prior to installing IIAB, make sure your `/etc/iiab/local_vars.yml <http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F>`_ contains::

  azuracast_install: True
  azuracast_enabled: True
