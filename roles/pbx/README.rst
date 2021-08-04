.. |ss| raw:: html

   <strike>

.. |se| raw:: html

   </strike>

.. |nbsp| unicode:: 0xA0
   :trim:

==========
PBX README
==========

This "pbx" playbook adds `Asterisk <https://asterisk.org/>`_ and `FreePBX <https://freepbx.org/>`_ to Internet-in-a-Box (IIAB) for VoIP and SIP functionality e.g. for rural telephony.

The initial release (for IIAB 6.7 in February 2019) supported Ubuntu 18.04, Debian 9 "Stretch" — and experimentally, Raspberry Pi: `#1467 <https://github.com/iiab/iiab/issues/1467>`_

*2021-08-02 GOOD NEWS: IIAB has upgraded from Asterisk 16.x (released 2018-10-09) to 18.x (released 2020-10-20*, `docs <https://wiki.asterisk.org/wiki/display/AST/Asterisk+18+Documentation>`_): `PR #2896 <https://github.com/iiab/iiab/pull/2896>`_

*2021-08-02 WORK IN PROGRESS: The latest versions of Ubuntu (20.04, 20.10, 21.04), Debian 11 "Bullseye" and the imminent Raspberry Pi OS 11 "Bullseye" all include PHP 7.4 — which does not work with FreePBX 15 — so IIAB is making the transition to* `FreePBX 16 Beta <https://www.freepbx.org/freepbx-16-beta-is-here/>`_ *which emerged on 2021-06-21:* `PR #2899 <https://github.com/iiab/iiab/pull/2899>`_

*PLEASE UNDERSTAND THIS MEANS THAT: IIAB no longer supports FreePBX 15 (i.e. Linux distros with PHP <= 7.3, e.g. on Raspberry Pi OS 10 "Buster").  Thank you for your understanding, as we look to the future together!*

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

After installing PBX as part of IIAB, please visit http://box.lan:83/freepbx and proceed with initial configuration (no login/password is required initially — you will be asked to set this up).

You can monitor the FreePBX service with command::

  systemctl status freepbx


Steps to setup a basic FreePBX configuration with a SIP extension
------------------------------------------------------------------
1. After installing PBX as part of IIAB, please visit http://box.lan:83/freepbx and proceed with initial configuration. You will be asked to setup your username and password the first time you login which will be used in future to login to the FreePBX configuration screen. Once you login, select the first option 'FreePBX Administrator'. 

2. Change the default asterisk password

    Go to Settings >> Asterisk settings. Click on 'Submit' button below and then clic'Apply config' that'll appear on the top right side of the web page. 


3. Change asterisk SIP settings

    Go to Settings >> Asterisk SIP settings >> Under NAT settings, clicking "Detect Network Settings" will populate your external IP
    Under Local networks, enter your local IP settings in the form of IP/CIDR or IP/NETMASK such as, “192.168.0.0/24" or “192.168.0.0/255.255.255.0”
    
    Click on 'Submit' button below and then click 'Apply config' that'll appear on the top right side of the web page.
    
    Refer - https://wiki.freepbx.org/display/FPG/Asterisk+SIP+Settings+User+Guide


4. Create SIP phone extensions to enable you to make calls within your network
    Go to Applications >> Extensions >> Add Extension >> New chan_pjsip extension

    **Extension** - <<An extension number of your choice, like 101>>

    **Display name** - <<Your name>>

    **Secret** - <<Add a strong password here>>
    
    Click on 'Submit' button below and then click 'Apply config' that'll appear on the top right side of the web page.

    Using the same steps, you could create more extensions for other users. 

5. Register the extension on your softphone app

    You can now register these extensions using a softphone app on your smartphone. For this example we will use the Linphone app on an Android phone

    Once you open the app, follow these steps

    1. Select option "USE SIP ACCOUNT"

    2. Enter the following details that you set in the FreePBX console
        Username - 101

        Password - Password you set for your extension

        Domain - Asterisk server IP address (To find this out, on the system where you've installed FreePBX, go to Terminal and run 'ifconfig' to find your IP address)

    3. Select "UDP" option under TRANSPORT
    4. Click on login. 
    5. If connection is successful, you will see 'connected' with a green cirle on the next screen
    6. Make a call to a random number or another extension you've created. You should be able to see activity on the applet at the right side of your FreePBX Dashboard

    Refer - https://wiki.freepbx.org/display/FPG/Extensions+Module+-+PJSIP+Extension

Troubleshooting
----------------
1. Check if asterisk is up and running
    Execute the command on your terminal and an asterisk console should open
    
    sudo asterisk -rvvv

2. If you see a "Asterisk not connected" in red on the FreePBX web console, check if asterisk is 'running' using this command on your terminal
    systemctl status asterisk

    If asterisk is not running (status does not show 'running'), restart asterisk

    sudo systemctl restart asterisk (confirm status shows up as running after executing this command)

3. If you see a "fwconsole read error" when you save settings, execute these commands on your terminal
    sudo fwconsole chown

    sudo fwconsole reload


4. Radcli error
    In files /etc/asterisk/cdr.conf and /etc/asterisk/cel.conf, this line sometimes needs to be added: (possibly this manual step is no longer necessary with Asterisk 18.x now!)

    radiuscfg => /etc/radcli/radiusclient.conf

    In any case, make 100% sure the file /etc/radcli/radiusclient.conf is non-empty. You can end up with a zero-length file here, if IIAB's roles/pbx install was interrupted (it should be about 2-to-3 kBytes initially). Probably best to start over with a clean OS in such situations!

    Also make sure any older lines including radiuscfg => /usr/local/etc/radiusclient-ng/radiusclient.conf are commented out within cdr.conf and cel.conf


Some useful asterisk commands and information 
----------------------------------------------
1. pjsip show endpoints
    This shows you the list of extensions along created on your FreePBX server along with its details

2. Asterisk log file is at /var/log/asterisk/full

3. If you do not see any activity on your asterisk console, you may need to increase the verbosity by executing either of these commands
    core set verbose 3, OR

    core set debug 3

4. To see all asterisk commands available
    core show help

5. To see all commands that start with core show
    ``core show [tab]`` or ``core show?``


Raspberry Pi Known Issues
-------------------------

|ss| As of 2019-02-14, "systemctl restart freepbx" failed more than 50% of the time when run on a `BIG-sized <http://wiki.laptop.org/go/IIAB/FAQ#What_services_.28IIAB_apps.29_are_suggested_during_installation.3F>`_ install of IIAB 6.7 on RPi 3 or RPi 3 B+.

It is possible that FreePBX restarts much more reliably when run on a MIN-sized install of IIAB?  Please `contact us <http://wiki.laptop.org/go/IIAB/FAQ#What_are_the_best_places_for_community_support.3F>`_ if you can assist here in any way: `#1493 <https://github.com/iiab/iiab/issues/1493>`_ |se|

Raspberry Pi Zero W Warning
---------------------------

Node.js applications like Asterisk/FreePBX, Node-RED and Sugarizer won't work on Raspberry Pi Zero W (ARMv6) if you installed Node.js while on RPi 3, 3 B+ (ARMv7) or RPi 4 (ARMv8).  If necessary, run ``apt remove nodejs`` or ``apt purge nodejs`` then ``rm /etc/apt/sources.list.d/nodesource.list; apt update`` then (`attempt! <https://nodered.org/docs/hardware/raspberrypi#swapping-sd-cards>`_) to `install Node.js <https://github.com/iiab/iiab/blob/master/roles/nodejs/tasks/main.yml>`_ *on the Raspberry Pi Zero W itself* (a better approach than "cd /opt/iiab/iiab; ./runrole nodejs" is to try ``apt install nodejs`` or try installing the tar file mentioned at `#2082 <https://github.com/iiab/iiab/issues/2082#issuecomment-569344617>`_).  You might also need ``apt install npm``.  Whatever versions of Node.js and npm you install, make sure ``/etc/iiab/iiab_state.yml`` contains the line ``nodejs_installed: True`` (add it if nec!)  Finally, proceed to install Asterisk/FreePBX, Node-RED and/or Sugarizer.  `#1799 <https://github.com/iiab/iiab/issues/1799>`_

Please also check the "Known Issues" at the bottom of `IIAB's latest release notes <https://github.com/iiab/iiab/wiki#our-evolution>`_.

Attribution
-----------

This "pbx" playbook was heavily inspired by Yannik Sembritzki's `Asterisk <https://github.com/Yannik/ansible-role-asterisk>`_ and `FreePBX <https://github.com/Yannik/ansible-role-freepbx>`_ Ansible work, Thank You!
