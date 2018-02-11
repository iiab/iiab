==============
usb-lib README
==============

PLEASE SEE "Can teachers display their own content?" WITHIN http://FAQ.IIAB.IO FOR UP-TO-DATE DOCUMENTATION.

This role implements functionality similar to LibraryBox, to mount "teacher content" on USB drives.

Users should have nearly immediate access to this "teacher content" (on all inserted USB drives) by browsing to http://box/usb

USB drives must be formatted with one of the iilesystems listed under "FILESYSTEMS=" at /etc/usbmount/usbmount.conf

Automount is handled by usbmount, and scripts in this role look in the root of the mounted drive for...

* /usb
* /USB
* /share
* /Share
* /Piratebox/Share

...and if found, creates a symlink of the form /library/www/html/local_content/USBn pointing to /media/usbn.

There is also a patch for problems with automount on Fedora 21+

Please Note that as of the 4.1.8-200.fc22.x86_64 not all USB drives will mount even with this patch.
