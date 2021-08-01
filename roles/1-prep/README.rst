=============
1-prep README
=============

This 1st `stage <https://github.com/iiab/iiab/wiki/IIAB-Contributors-Guide#ansible>`_ (1-prep) arranges low-level things like remote support infra, DNS prep, hardware, low-level OS quirks, and basic security:

- SSHD
- OpenVPN if/as needed later for remote support
- `iiab-admin <https://github.com/iiab/iiab/tree/master/roles/iiab-admin#iiab-admin-readme>`_ username and group, to log into Admin Console
- dnsmasq (install now, configure later!)
- Universally unique identifier: /etc/iiab/uuid
- Ubermix (distro) needs /etc/tmpfiles.d/iiab.conf to create essential /var/log subdirs on each boot
- Hardware actions:
   - `raspberry_pi.yml <tasks/raspberry_pi.yml>`_:
      - RTC (real-time clock): install udev rule, configure, enable
      - Install packages related to:
         - growpart
         - swapfile
         - fake-hwclock (as RTC is often missing or dead!)
         - Wi-Fi
      - Increase swap file size
      - rootfs auto-resizing
   - NUC 6 Wi-Fi firmware

Recap: Similar to 0-init, 2-common, 3-base-server, 4 server-options and 5-xo-services — this 1st stage installs core server infra (that is not user-facing).
