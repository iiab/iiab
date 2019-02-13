==========
PBX README
==========

This 'pbx' playbook adds `Asterisk <https://asterisk.org/>`_ and `FreePBX <https://freepbx.org/>`_ to Internet-in-a-Box (IIAB) for VoIP and SIP functionality e.g. for rural telephony.

This initial release (for IIAB 6.7 in February 2019) supports Ubuntu 18.04, Debian 9 "Stretch" — and experimentally supports Raspberry Pi: `#1467 <https://github.com/iiab/iiab/issues/1467>`_

What Asterisk & FreePBX Do
--------------------------

Asterisk is a software implementation of a private branch exchange (PBX).  In conjunction with suitable telephony hardware interfaces and network applications, Asterisk is used to establish and control telephone calls between telecommunication endpoints, such as customary telephone sets, destinations on the public switched telephone network (PSTN), and devices or services on Voice over Internet Protocol (VoIP) networks.  Its name comes from the asterisk (*) symbol for a signal used in dual-tone multi-frequency (DTMF) dialing. 

FreePBX is a web-based open source GUI (graphical user interface) that controls and manages Asterisk (PBX), the open source communication server.

Using It
--------

Prior to installing IIAB, make sure your `/etc/iiab/local_vars.yml <http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F>`_ contains::

  pbx_install: True
  pbx_enabled: True

Optionally, you may want to enable `chan_dongle <https://github.com/wdoekes/asterisk-chan-dongle>`_, which is a channel driver for Huawei UMTS cards allowing regular voice calls over GSM.  You will need to configure a dongle post-install, for it to be recognized properly::

  asterisk_chan_dongle: True

After installing PBX as part of IIAB, please visit http://pbx.lan/freepbx and proceed with initial configuration (no login/password is required initially — you will be asked to set this up).

**CAUTION: it is sometimes necessary to put "[ACTUAL IP ADDRESS] pbx.lan" into the 'hosts' file on the client machine (where the browser is being used) to get http://pbx.lan/freepbx to work.**  This file is ``/etc/hosts`` on Linux and macOS, or ``c:\Windows\System32\Drivers\etc\hosts`` on most Windows machines (conversely, customizing the hosts file is *not* necessary if your browser is able to access the `'LAN' side <https://github.com/iiab/iiab/wiki/IIAB-Networking#internet-in-a-box-iiab-networking>`_ of your IIAB server).

You can monitor the FreePBX service with command::

  systemctl status freepbx

Raspberry Pi Zero W Warning
---------------------------

Node.js applications like Sugarizer, Node-RED and Asterisk/FreePBX `won't work <https://nodered.org/docs/hardware/raspberrypi#swapping-sd-cards>`_ on Raspberry Pi Zero W (ARM6) if you installed Node.js while on RPi 3 or 3 B+ (ARM7).  If absolutely necessary, run "./runrole nodejs" from the Pi Zero W itself, before proceeding to install Sugarizer, Node-RED and/or Asterisk/FreePBX.

Attribution
-----------

This 'pbx' playbook was heavily inspired by Yannik Sembritzki's `Asterisk <https://github.com/Yannik/ansible-role-asterisk>`_ and `FreePBX <https://github.com/Yannik/ansible-role-freepbx>`_ Ansible work, Thank You!
