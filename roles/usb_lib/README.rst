==============
usb_lib README
==============

**PLEASE SEE "Can teachers display their own content?" WITHIN http://FAQ.IIAB.IO FOR UP-TO-DATE DOCUMENTATION.**

This role implements functionality similar to LibraryBox, to mount "teacher content" from USB drives.

Users should have nearly immediate access to this "teacher content" (on all inserted USB drives) by browsing to http://box/usb

Automount is handled by usbmount, and scripts in this role look in the root of the mounted drive for...

* /usb
* /USB
* /share
* /Share
* /Piratebox/Share

...and if found, creates a symlink of the form /library/www/html/local_content/USBn pointing to /media/usbn.

USB drives must be formatted with one of the filesystems listed under "FILESYSTEMS=" at ``/etc/usbmount/usbmount.conf`` — these are specified on/around Line 67 of: `/opt/iiab/iiab/roles/usb_lib/tasks/install.yml <https://github.com/iiab/iiab/blob/master/roles/usb_lib/tasks/install.yml#L67>`_

IIAB will generally mount USB drives 'rw' allowing root to both read and write to them.  In addition, in March 2021 (`PR #2715 <https://github.com/iiab/iiab/issues/2715>`_) Kolibri exports were enabled by also giving non-root users read and write access to VFAT/FAT32, NTFS and exFAT USB drives, using ``umask=0000`` (in /etc/usbmount/usbmount.conf) to override the ``umask=0022`` default.  If however you prefer to restore usbmount's default, set ``usb_lib_umask0000_for_kolibri: False`` in `/etc/iiab/local_vars.yml <http://FAQ.IIAB.IO/#What_is_local_vars.yml_and_how_do_I_customize_it.3F>`_ prior to installing IIAB.

Official `usbmount <https://github.com/hfuchs/usbmount>`_ documentation, from 2010:

* https://github.com/hfuchs/usbmount/blob/master/README
* https://github.com/hfuchs/usbmount/blob/master/usbmount.conf

Legacy warning: There is also a patch for problems with automount on Fedora 21+.  Please note that as of 4.1.8-200.fc22.x86_64 not all USB drives will mount, even with this patch.
