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

* Add the iiab-admin user and password
* N.B. to create password hash use python -c 'import crypt; print crypt.crypt("<plaintext>", "$6$<salt>")'
* Make a sudoer
* |ss| Add /root/.ssh and dummy authorized_keys file as placeholder |se| |nbsp| (moved to playbook roles/sshd)
* Force password for sudoers

Add Packages for Remote Access
------------------------------

* screen
* lynx

Admin Console
-------------

Has been moved to separate git repo: https://github.com/iiab/iiab-admin-console
