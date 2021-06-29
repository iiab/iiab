=============
1-prep README
=============

This 1st stage (1-prep) is primarily hardware-focused, prior to OS
additions/mods, but also includes critical pieces sometimes needed for
remote support:

- SSH
- `iiab-admin <https://github.com/iiab/iiab/tree/master/roles/iiab-admin>`_ username and group to log into Admin Console
- OpenVPN software if/as needed later for remote support

Traditionally 1-prep also included preliminaries like hostname and
hardware-oriented things specific to a particular platform (such as
One Laptop Per Child's XO laptop) i.e. critical setup prior to the
bulk of IIAB's software install.
