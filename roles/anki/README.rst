Anki Sync Server Role
=====================

This role installs a self-hosted Anki-compatible sync server behind IIAB's nginx
reverse proxy.

Usage
-----

Set the following in ``/etc/iiab/local_vars.yml`` before running IIAB:

.. code-block:: yaml

   anki_install: True
   anki_enabled: True
   anki_sync_users:
     - anki:changeme

Clients should then point their custom sync URL at ``http://box/anki/`` (note
the trailing slash, which Anki requires for subpath reverse proxies).
