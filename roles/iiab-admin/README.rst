.. |ss| raw:: html

   <strike>

.. |se| raw:: html

   </strike>

.. |nbsp| unicode:: 0xA0
   :trim:

=================
iiab-admin README
=================

`Internet-in-a-Box <http://internet-in-a-box.org>`_ (IIAB) encourages you to pay attention to the security of your learning community.

This Ansible playbook is one of the very first that runs when you install IIAB, and we hope reading this helps you understand your choices:

Configure user 'iiab-admin'
---------------------------

* `admin-user.yml <tasks/admin-user.yml>`_ configures a Linux user that will give you access to IIAB's Admin Console (http://box.lan/admin) after IIAB is installed — and can also help you at the command-line with IIAB community support commands like {iiab-diagnostics, iiab-hotspot-on, iiab-check-firmware, etc}.
   * If initial creation of the user and password was somehow not already taken care of by IIAB's 1-line installer (http://download.iiab.io) or by your underlying OS, that too will be taken care of here.
* By default this user is ``iiab-admin`` with password ``g0adm1n``
   * *Do change the default password if you haven't yet, by running:* **sudo passwd iiab-admin**
   * After IIAB is installed, you can also change the password by logging into Admin Console (http://box.lan/admin) > Utilities > Change Password.
* If you prefer to use a pre-existing user like ``pi`` or ``ubuntu`` (or any other username) customize the variable ``iiab_admin_user`` in your `/etc/iiab/local_vars.yml <http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F>`_ (preferably do this prior to installing IIAB!)
   * You can set ``iiab_admin_can_sudo: False`` if you want a strict security lockdown (if you're really sure you won't need IIAB community support commands like `/usr/bin/iiab-diagnostics <https://github.com/iiab/iiab/blob/master/scripts/iiab-diagnostics.README.md>`_, `/usr/bin/iiab-hotspot-on <https://github.com/iiab/iiab/blob/master/roles/network/templates/network/iiab-hotspot-on>`_, `iiab-check-firmware <https://github.com/iiab/iiab/blob/master/roles/firmware/templates/iiab-check-firmware>`_, etc!)
   * You can also set ``iiab_admin_user_install: False`` if you're sure you know how to do all this `account and sudo configuration <tasks/admin-user.yml>`_ manually.

Security
--------

* A user MUST be a member of at least one of these 2 Linux groups, in order to log in to IIAB's Admin Console: (http://box.lan/admin)
   #. ``iiab-admin`` (specified by ``admin_console_group`` near the bottom of `/opt/iiab/iiab-admin-console/vars/default_vars.yml <https://github.com/iiab/iiab-admin-console/blob/master/vars/default_vars.yml>`_)
   #. ``sudo``
* Please read much more about what escalated (root) actions are authorized when you log into IIAB's Admin Console, and how this works: https://github.com/iiab/iiab-admin-console/blob/master/Authentication.md
* If your IIAB includes OpenVPN, ``/root/.ssh/authorized_keys`` should be installed by `roles/openvpn/tasks/install.yml <https://github.com/iiab/iiab/blob/master/roles/openvpn/tasks/install.yml>`_ to faciliate remote community support.  Feel free to remove this as mentioned here: http://wiki.laptop.org/go/IIAB/Security
* Auto-checking for the default/published password (as specified by ``iiab_admin_published_pwd`` in `/opt/iiab/iiab/vars/default_vars.yml <https://github.com/iiab/iiab/blob/master/vars/default_vars.yml>`_) is implemented in `/etc/profile.d <https://github.com/iiab/iiab/blob/master/roles/iiab-admin/templates/sshpwd-profile-iiab.sh>`_ (and `/etc/xdg/lxsession/LXDE-pi <https://github.com/iiab/iiab/blob/master/roles/iiab-admin/templates/sshpwd-lxde-iiab.sh>`_ when it exists, i.e. on Raspberry Pi OS with desktop).

Example
=======

* If you later change your mind about ``sudo`` privileges for user 'iiab-admin' (as specified by ``iiab_admin_user``) then do this:
   #. Go ahead and change the value of ``iiab_admin_can_sudo`` (to either True or False) in `/etc/iiab/local_vars.yml <http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F>`_
   #. Make sure that ``iiab_admin_user_install: True`` is also set.
   #. Then re-run this Ansible playbook, by running ``cd /opt/iiab/iiab`` followed by ``sudo ./runrole --reinstall iiab-admin``

Historical Notes
================

* We no longer support setting your password using a hash e.g. ``python -c 'import crypt; print crypt.crypt("<plaintext>", "$6$<salt>")'`` (or the Python 3 equivalent, ``python3 -c 'import crypt; print(crypt.crypt("<plaintext>", crypt.mksalt(crypt.METHOD_SHA512)))'``) as these are very cumbersome — and worse, exposing your "salt" opens up your password to `possible attack <https://stackoverflow.com/questions/6776050/how-long-to-brute-force-a-salted-sha-512-hash-salt-provided>`_.  [October 2020]
* The sudo flag ``NOPASSWORD:`` and the ``wheel`` group are similarly no longer recommended, so that your IIAB faces fewer security risks.  [October 2020]

Tools to facilitate Remote Support
----------------------------------

The iiab-diagnostics and OpenVPN options mentioned can greatly help you help your community, typically during the implementation phase of your project, even if Linux is new to you.

Similarly, `/opt/iiab/iiab/roles/iiab-admin/tasks/access.yml <tasks/access.yml>`_ adds a couple text mode tools, very helpful at a distance with expensive / low-bandwidth connections:

* `lynx <https://en.wikipedia.org/wiki/Lynx_(web_browser)>`_
* `screen <https://linuxize.com/post/how-to-use-linux-screen/>`_

*More great tools to help you jumpstart community work at a distance:*

http://FAQ.IIAB.IO > "How can I remotely manage my Internet-in-a-Box?"

Admin Console
-------------

Has been moved to this separate git repo: https://github.com/iiab/iiab-admin-console
