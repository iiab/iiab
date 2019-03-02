=============
Lokole README
=============

This Ansible role installs the `Lokole web app <https://github.com/ascoderu/opwen-webapp>`_ within Internet-in-a-Box (IIAB).  Lokole is a project by the Canadian-Congolese non-profit `Ascoderu <https://ascoderu.ca>`_.

The Lokole is a simple email client that offers functionality like:

1. Self-service creation of user accounts
2. Read emails sent to the account
3. Write emails including rich formatting
4. Send attachments

The Lokole email client is translated into a number of languages, including French and Lingala.
For an up-to-date list of supported languages, refer to the `Lokole translations source <https://github.com/ascoderu/opwen-webapp/tree/master/opwen_email_client/webapp/translations>`_.

Using It
--------

The Lokole web app can be accessed at http://box/lokole

Administration
--------------

Log in with admin account: ``Admin``

By default, the password is: ``changeme``

Administrators can:

- Suspend and reinstate user accounts
- Reset passwords of non-admin user accounts
- Promote users to the admin role

All of these actions can be performed from the page http://box/lokole/users

Account Suspension
~~~~~~~~~~~~~~~~~~

Administrators have the ability to suspend and reinstate other users' accounts.  This functionality is useful for dealing with harassment, cyberbullying, and other forms of abuse.

Password Changes
~~~~~~~~~~~~~~~~

In the event of a data breach, administrators can update a user's password to a random string.  The user can then log in using this temporary password and change.  This functionality is also useful in the case that a user forgets their password.

Promoting and Demoting Users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Admins can grant and revoke admin privileges for other users.

Creating an Admin Account
~~~~~~~~~~~~~~~~~~~~~~~~~

To create a new admin account, run the following command::

  cd /library/lokole/venv
  ./python3 ./manage.py createadmin [--name | -n] <username> [--password | -p] <password>


Resetting the Database
~~~~~~~~~~~~~~~~~~~~~~

To reset the database, run the following command::

  cd /library/lokole/venv
  ./python3 ./manage.py resetdb

This command will remove all users and all emails from the system.

Troubleshooting
---------------

For further usage information and troubleshooting, refer to the `Lokole user manual <https://github.com/iiab/iiab/raw/master/roles/lokole/The%20Lokole-IIAB%20User's%20Manual.pdf>`_.

Known Issues
------------

For an up-to-date list of open issues, please see the `Lokole project's issue tracker <https://github.com/ascoderu/opwen-webapp/issues>`_.  See also `IIAB's issue tracker <https://github.com/iiab/iiab/issues>`_.
