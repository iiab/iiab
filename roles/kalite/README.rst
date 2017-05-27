==============
KA-Lite README
==============

This role installs KA-Lite, an offline version of the Khan Academy (https://www.khanacademy.org/),
written by Learning Equality (https://learningequality.org/ka-lite/).

KA Lite has two servers, a light httpd server that serves KA videos, and a cron server that sets
up cron jobs to download language packs and KA videos from the internet.  There are separate flags
to enable these two servers.

Access
------

If enabled and with the default settings KA Lite should be accessible at http://schoolserver:8008/

To login to kalite enter

User Name: Admin
Password: changme

Bulk Loading Videos
-------------------

Videos and their corresponding png images can be copied into /library/ka-lite/content and will
be recognized the next time kalite is started.  The kalite website has instructions on getting
videos with bitsync.  These videos are also smaller than the ones downloaded with the kalite
admin interface.

Configuration Parameters
------------------------

Please look in defaults/main.yml for the default values of the various install parameters.  Everything
in this readme assumes the default values.

Trouble Shooting
----------------

Starting with kalite 0.15 you can run the server manually with the following commands:

* systemctl stop kalite-serve (make sure the systemd service is not running)
* export KALITE_HOME=/library/ka-lite (point kalite to the right environment)
* kalite start (start the server; can take more than 10 minutes in some environment)

To return to using the systemd unit:

* export KALITE_HOME=/library/ka-lite (point kalite to the right environment)
* kalite stop
* systemctl start kalite-serve
