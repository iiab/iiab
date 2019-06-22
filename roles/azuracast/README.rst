==========
AzuraCast README
==========

This 'AzuraCast' playbook adds `AzuraCast <https://azuracast.com/>`_ to Internet-in-a-Box (IIAB) for network radio station functionality. With 'AzuraCast', one can schedule podcasts, music, and even do live streaming of audio content. A variety of streaming formats are supported.

Currently, this will only run on Ubuntu 18.04, Debian 9, Debian 10. This will not run on raspberry pi.

Using It
--------

**ISSUE!** Since the AzuraCast installer installs docker and docker-compose, it creates many network interfaces which confuses the IIAB network detection logic. So, it is highly recommended that to get AzuraCast, and a functional IIAB server, the following sequence be followed.

* Do a normal IIAB install with `azuracast_install` and `azuracast_enabled` set to `false`.
* Set the above variables to true.
* On the console, `./runrole azuracast` or a full IIAB install with `./iiab-install --reinstall`
* After the playbook completes, AzuraCast will be available on `http://box.lan:10080`
* Visiting that URL will prompt the user to do initial setup: user accounts, managing stations, radio streams, etc.

Note: When creating a station from the admin console. The default streaming ports for the `station` and `autodj` need to be in the port range 10000-10100.
