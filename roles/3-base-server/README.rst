====================
3-base-server README
====================

This 3rd stage installs base server infra that Internet-in-a-Box requires, including:

- MySQL (the database underlying many/most user-facing apps)
- NGINX web server (with Apache in some lingering cases)
- *PHP core packages are installed by the above 2 roles e.g. ``php{{ php_version }}-common``, ``php{{ php_version }}-cli``, ``php{{ php_version }}-fpm``, ``php{{ php_version }}-mysql``*

4-server-options follows with more diverse/optional server infra functionality.

As in the case of 2-common, 4-server-options and 5-xo-services: this stage installs core server infra, that is not user-facing.
