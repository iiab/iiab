=============
0-init README
=============

For a higher-level view of `Internet-in-a-Box (IIAB) <https://internet-in-a-box.org/>`_, please see http://FAQ.IIAB.IO and  `IIAB Installation <https://github.com/iiab/iiab/wiki/IIAB-Installation>`_.

This 0th `stage <https://github.com/iiab/iiab/wiki/IIAB-Contributors-Guide#ansible>`_ literally sets the stage for IIAB installation, prior to Ansible running Stages 1-to-9, which are typically then followed by the `network <../network>`_ stage.

But first: This 0th stage (0-init) serves to confirm low-level Ansible facts from the OS — e.g. for housekeeping tasks related to TZ (time zone), hostname, FQDN (fully-qualified domain name), unusual systemwide dependencies etc (and whether Internet is live) — so that IIAB installation can get underway.

Recap: Similar to 1-prep, 2-common, 3-base-server, 4-server-options and 5-xo-services ⁠— this 0th stage installs core server infra (that is not user-facing).
