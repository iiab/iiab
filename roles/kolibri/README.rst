==============
Kolibri README
==============

This role installs Kolibri, an open-source educational platform specially designed
to provide offline access to a wide range of quality, openly licensed educational
contents in low-resource contexts like rural schools, refugee camps, orphanages,
and also in non-formal school programs.

Access
------

If enabled and with the default settings Kolibri should be accessible at http://box:8009

To login to Kolibri enter

  Username: Admin
  
  Password: changeme

Configuration Parameters
------------------------

Please look in defaults/main.yml for the default values of the various install parameters.  Everything
in this readme assumes the default values.

Automatic Device Provisioning
-----------------------------

When kolibri_provision is enabled, the installation will setup the following settings:

  Kolibri Facility name: 'Kolibri-in-a-Box'

  Kolibri Preset type: formal (Other options are nonformal, informal)

  Kolibri default language: en (Otherwise language are ar,bn-bd,en,es-es,fa,fr-fr,hi-in,mr,nyn,pt-br,sw-tz,ta,te,ur-pk,yo,zu)

  Kolibri Admin User: Admin

  Kolibri Admin password: changeme

Cloning content
---------------

Kolibri 0.10 introduced `kolibri manage deprovision` which will remove
user configuration, leaving content intact. You can then copy/clone /library/kolibri
to a new location.

Troubleshooting
----------------

You can run the server manually with the following commands:

  systemctl stop kolibri (make sure the systemd service is not running)

  export KOLIBRI_HOME=/library/kolibri

  export KOLIBRI_HTTP_PORT=8009 (otherwise Kolibri will try to run on default port 8080)

  kolibri start

To return to using the systemd unit:

  kolibri stop

  systemctl start kolibri
