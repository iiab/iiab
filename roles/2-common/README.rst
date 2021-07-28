===============
2-common README
===============

This 2nd `stage <https://github.com/iiab/iiab/wiki/IIAB-Contributors-Guide#ansible>`_ is for OS-level basics *common* to all platforms, i.e. core prerequisites to building up a functioning `Internet-in-a-Box (IIAB) <https://internet-in-a-box.org/>`_ server.

These are (partially) put in place:

- IIAB directory structure (`file layout <tasks/fl.yml>`_)
- Common `apt <https://en.wikipedia.org/wiki/APT_(software)>`_ software packages
- Networking (including the `iptables <https://en.wikipedia.org/wiki/Iptables>`_ firewall)
- `/usr/libexec/iiab-startup.sh <tasks/iiab-startup.yml>`_ similar to AUTOEXEC.BAT and /etc/rc.local, in order to run jobs on boot

Recap: as with 0-init, 1-prep, 3-base-server, 4-server-options and 5-xo-services, this 2nd stage installs core server infra (that is not user-facing).
