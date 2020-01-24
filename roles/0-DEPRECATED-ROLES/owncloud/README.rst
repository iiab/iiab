===============
Owncloud README
===============

This role installs Owncloud, a local cloud type server to share files, calendars, and contacts.

Configuration Parameters
------------------------

The following are set as defaults in var/main.yml:

* owncloud_install: True
* owncloud_enabled: False
* owncloud_prefix: "/opt"
* owncloud_data_dir: /library/owncloud/data
* owncloud_src_file: owncloud-7.0.12.tar.bz2

* owncloud_admin_user: 'Admin'
* owncloud_admin_password: 'changeme'

We install on mysql with these setting or those from default_vars, etc.

* owncloud_dbname: owncloud
* owncloud_dbhost: localhost
* owncloud_dbuser: owncloud
* owncloud_dbpassword: owncloudmysql

Access and Installation Wizard
------------------------------

The ansible installation performs the Owncloud Wizard.

After the ansible installation completes, you can access Owncloud at http://schoolserve/owncloud.

The default admin user name and password are Admin / changeme.

Login and change the password.  You can now add users and start sharing content.
