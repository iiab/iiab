==============
usb-lib README
==============

SEE "Can teachers display their own content?" WITHIN http://FAQ.IIAB.IO FOR UP-TO-DATE DOCUMENTATION.

This role implements functionality similar to LibraryBox, to mount and link content on a USB drive within /library/www/html/local_content

Users should have nearly immediate access to "teacher content" by browsing to http://box/usb

Automount is handled by usbmount and scripts in this role look in the root of the mounted drive for

* /usb
* /USB
* /share
* /Share
* /Piratebox/Share

and if found create a symlink of the form /library/content/USBn points to /media/usbn.

There is also a patch for problems with automount on Fedora 21+

Please Note that as of the 4.1.8-200.fc22.x86_64 not all USB drives will mount even with this patch.
