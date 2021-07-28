=============
1-prep README
=============

This 1st `stage <https://github.com/iiab/iiab/wiki/IIAB-Contributors-Guide#ansible>`_ (1-prep) is primarily hardware-focused, prior to OS
additions/mods — but also includes critical pieces sometimes needed for
remote support:

- dnsmasq
- /etc/iiab/uuid
- Customizing /var/log/* for Ubermix on each boot, using /etc/tmpfiles.d
- SSH
- `iiab-admin <https://github.com/iiab/iiab/tree/master/roles/iiab-admin>`_ username and group to log into Admin Console
- OpenVPN software if/as needed later for remote support
- `raspberry_pi.yml <tasks/raspberry_pi.yml>`_ including RTC, essential packages, and networking basics

Traditionally 1-prep also included preliminaries like hostname and
hardware-oriented things specific to a particular platform (such as
One Laptop Per Child's XO laptop) i.e. critical setup prior to the
bulk of IIAB's software install.

Recap: Similar to 0-init, 2-common, 3-base-server, 4 server-options and 5-xo-services ⁠— this 1st stage installs core server infra (that is not user-facing).
