=================
XSCE Admin README
=================

This role is home to a number of administrative playbooks.  Those implemented are:

Add Administrative User
-----------------------

* Add the xsce-admin user and password
* N.B. to create password hash use python -c 'import crypt; print crypt.crypt("<plaintext>", "$6$<salt>")'
* Make a sudoer
* Add /root/.ssh and dummy authorized_keys file as placeholder
* Force password for sudoers

Add Packages for Remote Access
------------------------------

* screen
* lynx

Admin Console
-------------

Has been moved to a separate git repo