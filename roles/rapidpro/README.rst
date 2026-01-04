RapidPro Role
=============

This role installs and configures RapidPro, a platform for building and managing mobile-based services.

Requirements
------------

This role requires the following:

*   Debian/Ubuntu-based system
*   PostgreSQL
*   Nginx
*   Redis or Valkey

These dependencies are automatically installed by this role.

Role Variables
--------------

*   ``rapidpro_install``: Set to ``True`` to install RapidPro. Default is ``True``.
*   ``rapidpro_enabled``: Set to ``True`` to enable and start the RapidPro services. Default is ``True``.
*   ``rapidpro_db_name``: The name of the PostgreSQL database for RapidPro. Default is ``temba``.
*   ``rapidpro_db_user``: The PostgreSQL user for the RapidPro database. Default is ``temba``.
*   ``rapidpro_db_pass``: **MANDATORY**. The password for the PostgreSQL user. Must be set in ``local_vars.yml``.
*   ``admin_email``: The email address for the RapidPro admin user. Default is ``admin@box.lan``.
*   ``rapidpro_admin_password``: **MANDATORY**. The password for the RapidPro admin user. Must be set in ``local_vars.yml``.
*   ``rapidpro_secret_key``: **MANDATORY**. The Django SECRET_KEY. Must be set in ``local_vars.yml``.
*   ``rapidpro_url``: The URL path for RapidPro. Default is ``/rp``.

Security Notice
---------------

**CRITICAL**: This role does not provide default passwords for security reasons. You **MUST** define the following variables in ``/etc/iiab/local_vars.yml`` before installation:

.. code-block:: yaml

    rapidpro_db_pass: "your_secure_db_password"
    rapidpro_admin_password: "your_secure_admin_password"
    rapidpro_secret_key: "your_long_random_secret_key"
    wuzapi_admintoken: "your_secure_admin_token"  # Required for Wuzapi integration

Usage
-----

To install and enable RapidPro, add the configuration above to your ``/etc/iiab/local_vars.yml`` and run the installer:

.. code-block:: bash

    ./runrole rapidpro wuzapi

Then run the IIAB installer.

After installation, RapidPro will be available at ``http://box.lan/rp``.