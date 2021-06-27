====================
3-base-server README
====================

This 3rd stage installs base server infra that Internet-in-a-Box requires, including:

- MySQL (database underlying many/most user-facing apps)
- NGINX web server (with Apache in some lingering cases)
- *A few core PHP packages are also installed by the above 2 roles, e.g.*
   - php{{ php_version }}-common
   - php{{ php_version }}-cli
   - php{{ php_version }}-fpm
   - php{{ php_version }}-mysql

As with 2-common, 4-server-options and 5-xo-services: this stage installs core server infra, that is not user-facing.

The next stage (4-server-options) brings more diverse/optional server infra functionality.
