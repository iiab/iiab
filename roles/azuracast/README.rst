================
AzuraCast README
================

This playbook adds `AzuraCast <https://azuracast.com/>`_ to Internet-in-a-Box (IIAB) for network radio station functionality.  With 'AzuraCast' you and your community can schedule podcasts, music, and even do live streaming of audio content.  A variety of streaming formats are supported.

Please see AzuraCast's `screenshots <https://www.azuracast.com/about/screenshots.html>`_.

As of 2019-08-04, this will only run on Ubuntu 18.04, and tentatively on Debian 10 "Buster" (`#1766 <https://github.com/iiab/iiab/issues/1766>`_).  Support for Raspberry Pi remains a goal for now — please if you can, consider helping us solve this critical challenge (`#1772 <https://github.com/iiab/iiab/issues/1772>`_, `AzuraCast/AzuraCast#332 <https://github.com/AzuraCast/AzuraCast/issues/332>`_).

Using It
--------

* Do a normal IIAB install (https://download.iiab.io), making sure to set both variables ``azuracast_install`` and ``azuracast_enabled`` to ``True`` when it prompts you to edit `/etc/iiab/local_vars.yml <http://FAQ.IIAB.IO#What_is_local_vars.yml_and_how_do_I_customize_it.3F>`_, as you begin the installation.
* When the IIAB software install completes, it will ask you to reboot, and AzuraCast's console will then be available at http://box.lan:12080
* This console site will prompt you to complete AzuraCast's initial setup: user accounts, managing stations, radio streams, etc.
* Finally, check out some `how-to videos <https://www.youtube.com/watch?v=b1Rxlu5P804>`_ to learn to manage your own radio station!

Note: When creating a station using AzuraCast's console, its default streaming ports for ``station`` and ``autodj`` need to be in the `port range 10000-10100 <https://github.com/iiab/iiab/wiki/IIAB-Networking#list-of-ports--services>`_.
