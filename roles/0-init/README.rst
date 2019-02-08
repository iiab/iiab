=============
0-init README
=============

For a higher-level view, please see `IIAB Installation <https://github.com/iiab/iiab/wiki/IIAB-Installation>`_ and http://FAQ.IIAB.IO

This 0th stage literally sets the stage for Internet-in-a-Box (IIAB) installation, prior to Ansible running `Stages 1-to-9 <.>`_ and then the `network <network>`_ stage.

This serves to confirm low-level Ansible facts from the OS — e.g. for housekeeping tasks related to TZ (time zone), hostname, FQDN (fully-qualified domain name), unusual systemwide dependencies etc — and whether Internet is live so that IIAB installation can proceed.
