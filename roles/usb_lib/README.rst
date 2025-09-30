==============
usb_lib README
==============

**PLEASE SEE** `"Can teachers display their own content?" <https://wiki.iiab.io/go/FAQ#Can_teachers_display_their_own_content?>`_ **AND** `"Can students upload their own work?" <https://wiki.iiab.io/go/FAQ#Can_students_upload_their_own_work?>`_ **WITHIN https://FAQ.IIAB.IO FOR UP-TO-DATE DOCUMENTATION!**

This role (1) implements functionality similar to LibraryBox, to mount "teacher content" from USB sticks / drives for students, and (2) allows students to upload their work to the teacher's USB stick / drive:

#. Students should have nearly immediate access to "teacher content" (on all inserted USB sticks) by browsing to: http://box/usb
#. Students can also click the "Upload to USB" button on top of this same page (http://box/usb), to upload their work to the teacher's USB stick.  (FYI student uploads appear in folders like ``UPLOADS.YYYY-MM-DD`` within the root of the teacher's USB stick).

As of September 2025, automount is handled by usbmount: (`devmon included with udevil <https://ignorantguru.github.io/udevil/>`_ might be considered in future)

* A script in this role (/etc/usbmount/mount.d/70-usb-library) looks in the root of the mounted USB stick for folder /PUBLIC and if found, creates a symlink of the form /library/www/html/local_content/USBn pointing to /media/usbn/PUBLIC — where n is generally one of {0, 1, 2, 3, 4, 5, 6, 7}.  *RESULT: Only documents within /PUBLIC are browsable by students.*  This option is very useful to **prevent students from copying uploaded homework!**
* If however folder /PUBLIC is not found, the symlink is created to the root of the mounted USB stick.  *RESULT: EVERYTHING on the USB stick is browsable by students — just like with a traditional community bulletin board.*  This option is very useful when students are uploading artwork, photo essays, personal audio recordings and **science projects that are intended to be shared!**

Technical Details:

* USB sticks / drives must be formatted with one of the filesystems listed under "FILESYSTEMS=" at ``/etc/usbmount/usbmount.conf`` — these are specified on/around Line 17 of: `/opt/iiab/iiab/roles/usb_lib/files/usbmount/usbmount.conf <https://github.com/iiab/iiab/blob/master/roles/usb_lib/files/usbmount/usbmount.conf#L17>`_

* If your IIAB was built on a Graphical Desktop OS (instead of a headless OS, like Raspberry Pi OS Lite), USB sticks will sometimes problematically be mounted twice by default, once by usbmount and once by the desktop.  You must disable the automount function in the Desktop in order to use the "Upload to USB" functionality, which allows students to upload their work to your USB stick. (`Issue #4066 <https://github.com/iiab/iiab/issues/4066>`_)

  * As of August 2025, these Graphical Desktop OS's double mount USB sticks after IIAB is installed: Ubuntu 24.04, Ubuntu 25.10, Debian 13, Linux Mint 22.2, and Raspberry Pi OS Bookworm. Conversely, Raspberry Pi OS Trixie (with desktop) **TRIES** to avoid double mounting USB sticks.
  * EXAMPLE: To disable Desktop automount within Ubuntu 24.04, 25.10 or Debian 13, install dconf-editor with ``apt install dconf-editor``. Open up dconf-editor from the OS's Applications menu. In the dconf-editor window, navigate through the folders: org → gnome → desktop → media-handling. Set ``automount`` and ``automount-open`` to false. In Linux Mint 22.2, navigate to ``cinnamon`` instead of ``gnome``. 

    * **WARNING:** Using dconf-editor that was opened from the command line may not work. In at least Linux Mint, there are `known syncing issues <https://github.com/iiab/iiab/issues/4066#issuecomment-3238784694>`_ between the application opened by the command line and the one opened by the Applications menu.
  * EXAMPLE: To disable Desktop automount within "Raspberry Pi OS Bookworm (with graphical desktop)", go to File Manager (pcmanfm) → Edit → Preferences → Volume Management, and uncheck "Mount removable media automatically when they are inserted".

* IIAB will generally mount USB sticks / drives 'rw' allowing root to both read and write to them.  In addition, in March 2021 (`PR #2715 <https://github.com/iiab/iiab/pull/2715>`_) Kolibri exports were enabled, by also giving non-root users read and write access to VFAT/FAT32, NTFS and exFAT USB sticks — using ``umask=0000`` (in /etc/usbmount/usbmount.conf) to override the ``umask=0022`` default.  This ``umask=0000`` is also required for students to upload to the teachers's VFAT/FAT32, NTFS and exFAT USB sticks, as introduced in January 2025 (`PR #3875 <https://github.com/iiab/iiab/pull/3875>`_).  If, however, you prefer to restore usbmount's default, set ``usb_lib_writable_sticks: False`` in `/etc/iiab/local_vars.yml <http://FAQ.IIAB.IO/#What_is_local_vars.yml_and_how_do_I_customize_it%3F>`_ — please do this prior to installing IIAB — so you don't have to run: ``cd /opt/iiab/iiab ; ./runrole --reinstall usb_lib``

* Official `usbmount 0.0.22 (2011-08-08) <https://github.com/rbrito/usbmount/tags>`_ documentation:

  * https://github.com/hfuchs/usbmount/blob/master/README (2010-08-11)
  * https://github.com/rbrito/usbmount/blob/master/README.md (2018-08-10)
  * https://github.com/rbrito/usbmount/blob/master/usbmount.conf (2010-04-25)

* Dev Notes at the top of: https://github.com/iiab/iiab/blob/master/roles/usb_lib/tasks/install.yml

  * January 2025 work to improve automount reliability during boot: `PR #3916 <https://github.com/iiab/iiab/pull/3916>`_
