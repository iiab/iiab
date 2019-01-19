===============
PBX README
===============

Adds `Asterisk <https://asterisk.org/>`_ and `FreePBX <https://freepbx.org/>`_ to Internet-in-a-Box (IIAB) for VoIP and SIP functionality.

Asterisk is a software implementation of a private branch exchange (PBX). In conjunction with suitable telephony hardware interfaces and network applications, Asterisk is used to establish and control telephone calls between telecommunication endpoints, such as customary telephone sets, destinations on the public switched telephone network (PSTN), and devices or services on voice over Internet Protocol (VoIP) networks. Its name comes from the asterisk (*) symbol for a signal used in dual-tone multi-frequency (DTMF) dialing. 

FreePBX is a web-based open source GUI (graphical user interface) that controls and manages Asterisk (PBX), an open source communication server.

Using It
--------

Prior to installing IIAB, make sure your `/etc/iiab/local_vars.yml <http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F>`_ contains::

  pbx_install: True
  pbx_enabled: True
  nodejs_version: 10.x

As a dependency the following must be set::
  
  sugarizer_install: False
  sugarizer_enabled: False


After installing PBX as part IIAB, please log in to http://pbx.lan and proceed with inital configuration.

You can monitor the PBX service with command::

  systemctl status freepbx

Attribution
-----------

The asterisk and freepbx playbooks have been heavily inspired by the work `here <https://github.com/Yannik/ansible-role-asterisk>`_ and `here <https://github.com/Yannik/ansible-role-freepbx>`_. 
Dependencies
------------

1. This playbooks compiles and installs asterisk and freepbx from source, so running this feature involves significant bandwidth and compute time.
2. This playbook is also incompatible with sugarizer, and nodejs-8.x. Therefore if either of those are set to be install, this playbook will gracefully fail with a message requesting the user to fix those incompatibilites. 
