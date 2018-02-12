==============
usb-lib README
==============

PLEASE SEE "Can teachers display their own content?" WITHIN http://FAQ.IIAB.IO FOR UP-TO-DATE DOCUMENTATION.

This role implements functionality similar to LibraryBox, to mount "teacher content" from USB drives.

Users should have nearly immediate access to this "teacher content" (on all inserted USB drives) by browsing to http://box/usb

Automount is handled by usbmount, and scripts in this role look in the root of the mounted drive for...

* /usb
* /USB
* /share
* /Share
* /Piratebox/Share

...and if found, creates a symlink of the form /library/www/html/local_content/USBn pointing to /media/usbn.

USB drives must be formatted with one of the filesystems listed under "FILESYSTEMS=" at /etc/usbmount/usbmount.conf

WARNING: even after adding "exfat ntfs fuseblk" within the above line, problems remain automounting exFAT and NTFS filesystems using usbmount, as of February 2018.  It's recommended you stick to FAT32 and ext4 filesystems for now.

There is also a patch for problems with automount on Fedora 21+

Please Note that as of the 4.1.8-200.fc22.x86_64 not all USB drives will mount even with this patch.
