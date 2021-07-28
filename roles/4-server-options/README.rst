=======================
4-server-options README
=======================

Whereas 3-base-server installs critical packages needed by all, this 4th `stage <https://github.com/iiab/iiab/wiki/IIAB-Contributors-Guide#ansible>`_ installs a broad array of *options* ⁠— depending on which server apps will be installed in later stages ⁠— as specified in `/etc/iiab/local_vars.yml <http://FAQ.IIAB.IO#What_is_local_vars.yml_and_how_do_I_customize_it.3F>`_

This includes more networking fundamentals, that may further be configured later on.

Specifically, these might be installed:

- Python libraries
- SSH daemon
- Bluetooth for Raspberry Pi
- Instant-sharing of `USB stick content <https://wiki.iiab.io/go/FAQ#Can_teachers_display_their_own_content.3F>`_
- CUPS Printing
- Samba for Windows filesystems
- `www_options <https://github.com/iiab/iiab/blob/master/roles/www_options/tasks/main.yml>`_

Recap: as in the case of 0-init, 1-prep, 2-common, 3-base-server and 5-xo-services ⁠— this 4th stage installs core server infra (that is not user-facing).
