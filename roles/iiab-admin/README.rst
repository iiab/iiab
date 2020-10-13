.. |ss| raw:: html

   <strike>

.. |se| raw:: html

   </strike>

.. |nbsp| unicode:: 0xA0
   :trim:

=================
iiab-admin README
=================

This role is home to a number of administrative playbooks.  Those implemented are:

Add Administrative User
-----------------------

* Add the iiab-admin user and password, if this has not already been done for you by IIAB's 1-line installer
* |ss| N.B. to create password hash use python -c 'import crypt; print crypt.crypt("<plaintext>", "$6$<salt>")' |se| |nbsp| (not recommended as of October 2020)
* |ss| Make a sudoer |se| |nbsp| (likely going away in October 2020, group 'iiab-admin' will be recommended instead of group 'sudo')
* |ss| Add /root/.ssh and dummy authorized_keys file as placeholder |se| |nbsp| (moved to playbook roles/sshd)
* |ss| Force password for sudoers |se|
* Please read more about the 'iiab-admin' Linux user and group, which allow you to log in to IIAB's Admin Console: https://github.com/iiab/iiab-admin-console/blob/master/Authentication.md

Add Packages for Remote Access
------------------------------

* screen
* lynx

Admin Console
-------------

Has been moved to separate git repo: https://github.com/iiab/iiab-admin-console
