.. |ss| raw:: html

   <strike>

.. |se| raw:: html

   </strike>

.. |nbsp| unicode:: 0xA0
   :trim:

=================
iiab-admin README
=================

This role is home to a number of administrative (Ansible) playbooks:

Add Administrative User
-----------------------

* Adds the Linux user that will allow you access to IIAB's Admin Console (http://box.lan/admin) if this has not already been done for you by IIAB's 1-line installer (http://download.iiab.io).
* By default this is ``iiab-admin`` with password ``g0adm1n``
   * *Do change the default password if you haven't yet, by running:* **sudo passwd iiab-admin**
   * After IIAB is installed, you can also change the password by logging into Admin Console (http://box.lan/admin) > Utilities > Change Password
   * If you prefer using a pre-existing user like ``pi`` or ``ubuntu`` etc, consider customizing variables ``iiab_admin_user_install``, ``iiab_admin_user`` and ``iiab_admin_user_group`` in your `/etc/iiab/local_vars.yml <http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F>`_ (please do this prior to installing IIAB !)
* Please read more about what escalated (root) actions are authorized when you log into IIAB's Admin Console, and how this works: https://github.com/iiab/iiab-admin-console/blob/master/Authentication.md

Desiderata, for the historical record:

* Auto-checking for the default password is implemented in `/etc/profile.d <https://github.com/iiab/iiab/blob/master/roles/iiab-admin/templates/sshpwd-profile-iiab.sh>`_ (and `/etc/xdg/lxsession/LXDE-pi <https://github.com/iiab/iiab/blob/master/roles/iiab-admin/templates/sshpwd-lxde-iiab.sh>`_ when it exists).
* |ss| N.B. to create password hash use python -c 'import crypt; print crypt.crypt("<plaintext>", "$6$<salt>")' |se| |nbsp| (not recommended as of October 2020)
* |ss| Make a sudoer |se| |nbsp| (likely going away in October 2020, as group 'iiab-admin' should be recommended instead of group 'sudo')
* |ss| Add /root/.ssh and dummy authorized_keys file as placeholder |se| |nbsp| (moved to `roles/openvpn/tasks/install.yml <https://github.com/iiab/iiab/blob/master/roles/openvpn/tasks/install.yml>`_)
* |ss| Force password for sudoers |se| |nbsp| (sudo flag ``NOPASSWORD:`` and the ``wheel`` group will no longer being used as of October 2020)

Add Packages for Remote Access
------------------------------

* screen
* lynx

Admin Console
-------------

Has been moved to this separate git repo: https://github.com/iiab/iiab-admin-console
