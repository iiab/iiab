=============
Lokole README
=============

This Ansible role installs the `Lokole web app <https://github.com/ascoderu/lokole>`_ within Internet-in-a-Box (IIAB).  Lokole is a project by the Canadian-Congolese non-profit `Ascoderu <https://ascoderu.ca>`_.

The Lokole is a simple email client that offers functionality like:

1. Self-service creation of user accounts
2. Read emails sent to the account
3. Write emails including rich formatting
4. Send attachments

The Lokole email client is translated into a number of languages, including French and Lingala.
For an up-to-date list of supported languages, refer to the `Lokole translations source <https://github.com/ascoderu/lokole/tree/master/opwen_email_client/webapp/translations>`_.

Using It
--------

If your IIAB was `installed <http://wiki.laptop.org/go/IIAB/FAQ#Is_a_quick_installation_possible.3F>`_ with the Lokole web app[*] it can be accessed at http://box/lokole

[*] If you're not sure, verify that your IIAB's `/etc/iiab/local_vars.yml <http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F>`_ contains ``lokole_install: True`` and ``lokole_enabled: True``

By default in an offline community, ``lokole_sim_type: LocalOnly`` is set (e.g. instead of ``lokole_sim_type: Ethernet``) and email addresses will look like:

``joe@none.lokole.ca``

2021-05-15: in future, communities should be able to customize their subdomain, to set up Internet-capable email addresses like:

``sue@kinshasalibrary.lokole.ca``

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

Nightly Internet Email Sync (Not Easy!)
---------------------------------------

The Lokole software can be configured to access the Internet via USB modem, SIM card, or Ethernet, by setting the environment variable ``OPWEN_SIM_TYPE`` in configuration file `/home/lokole/state/webapp_secrets.sh <https://github.com/iiab/iiab/blob/master/roles/lokole/templates/webapp_secrets.sh.j2>`_.  By default, this installation of Lokole is set to local-only (offline) mode, in which users can only send emails to other users on the same Internet-in-a-Box, and cannot send emails over the Internet.  This has been done by setting ``OPWEN_SIM_TYPE`` to ``LocalOnly``.

If configured to work with a USB modem or other form of Internet connection, Lokole will sync with the cloud server (operated by `Ascoderu <https://ascoderu.ca/>`_) on a nightly basis to deliver and receive emails globally.  *However, arranging this is extremely complicated.*  You would need a compatible form of connection and an Internet expert familiar with modem protocols, MX records, etc.  Ask that person to read the `Lokole software README <https://github.com/ascoderu/lokole/blob/master/README.rst>`_ in its entirety, to help you understand whether this is realistic for your organization.

Lokole and Internet-in-a-Box would welcome a business plan (whether volunteer-based, grant-based or for-profit) from someone willing to operationalize this — making it relatively hassle-free for schools, clinics, libraries and orphanages around the world — that generally do not have access to technical experts.  Please `contact us <http://wiki.laptop.org/go/IIAB/FAQ#What_are_the_best_places_for_community_support.3F>`_ if you have the capacity to help make such a social enterprise happen.

Troubleshooting
---------------

For further usage information and troubleshooting, refer to the `Lokole user manual <Lokole-IIAB_Users_Manual.pdf>`_.

Known Issues
------------

For an up-to-date list of open issues, please see the `Lokole project's issue tracker <https://github.com/ascoderu/lokole/issues>`_.  See also `IIAB's issue tracker <https://github.com/iiab/iiab/issues>`_.
