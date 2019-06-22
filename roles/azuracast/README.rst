==========
AzuraCast README
==========

This 'AzuraCast' playbook adds `AzuraCast <https://azuracast.com/>`_ to Internet-in-a-Box (IIAB) for network radio station functionality.  With 'AzuraCast' you and your community can schedule podcasts, music, and even do live streaming of audio content.  A variety of streaming formats are supported.

Currently, this will only run on Ubuntu 18.04, Debian 9, Debian 10.  At present, it will not run on Raspberry Pi.

Using It
--------

**ISSUE!**  Since the AzuraCast installer installs docker and docker-compose, it creates many network interfaces which confuse the IIAB network detection logic (`#1753 <https://github.com/iiab/iiab/pull/1753>`_).  So, as of 2019-06-21, follow this sequence to get AzuraCast working on your IIAB server:

* Do a normal IIAB install (http://download.iiab.io) keeping ``azuracast_install`` and ``azuracast_enabled`` False, per the defaults.
* Set the two above variables to True in `/etc/iiab/local_vars.yml <http://FAQ.IIAB.IO#What_is_local_vars.yml_and_how_do_I_customize_it.3F>`_
* As root, do ``cd /opt/iiab/iiab`` then ``./runrole azuracast`` (or do ``./iiab-install --reinstall`` for a full IIAB install)
* After the Ansible playbook completes, AzuraCast's console will be available on http://box.lan:10080
* This site will prompt you to set up: user accounts, managing stations, radio streams, etc.

Note: When creating a station from AzuraCast's console, its default streaming ports for ``station`` and ``autodj`` need to be in the `port range 10000-10100 <https://github.com/iiab/iiab/wiki/IIAB-Networking#list-of-ports--services>`_.
