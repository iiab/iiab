=============
RACHEL README
=============

This is the second pass at adding RACHEL (http://www.rachel.worldpossible.org/) to XSCE.
It takes RACHEL in its entirety and the download must be copied manually.
This version is based on rachelusb_32EN_3.1.5.zip.

Do the following:

* Uuzip rachelusb_32EN_3.1.5.zip into /library.  You should get /library/rachelusb_32EN_3.1.4.
* mkdir /library/rachel
* cd /library/rachel
* mv /library/rachelusb_32EN_3.1.4/RACHEL/bin .
* you should see /library/rachel/bin/www/index.php
* re-run ansible (making sure that rachel_enabled: True has been set in /etc/iiab/local_vars.yml

Locations
---------

- The RACHEL download is expected to be in /library/rachel
- The URL is /rachel
