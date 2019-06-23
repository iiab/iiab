==========
AzuraCast README
==========

This 'AzuraCast' playbook adds `AzuraCast <https://azuracast.com/>`_ to Internet-in-a-Box (IIAB) for network radio station functionality.  With 'AzuraCast' you and your community can schedule podcasts, music, and even do live streaming of audio content.  A variety of streaming formats are supported.

Currently, this will only run on Ubuntu 18.04, Debian 9, Debian 10.  At present, it will not run on Raspberry Pi.

Using It
--------

* Do a normal IIAB install (http://download.iiab.io) keeping variables ``azuracast_install`` and ``azuracast_enabled`` as True.
* AzuraCast's console will be available at http://box.lan:10080
* This site will prompt you to complete initial setup: user accounts, managing stations, radio streams, etc.

Note: When creating a station using AzuraCast's console, its default streaming ports for ``station`` and ``autodj`` need to be in the `port range 10000-10100 <https://github.com/iiab/iiab/wiki/IIAB-Networking#list-of-ports--services>`_.
