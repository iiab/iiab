===========
Elgg README
===========

Elgg is an award-winning social networking engine, delivering the building blocks
that enable businesses, schools, universities and associations to create their own
fully-featured social networks and applications.

https://elgg.org

After Installation
------------------

Go to http://box/elgg or http://box.lan/elgg and log on as Admin with password changeme.

Change the following:

* Administrator password

* Title to appear on Elgg screens and any other settings as desired.

Locations
---------

- The uploaded files are expected to be in /library/elgg
- The software is in /opt/elgg -> /opt/elgg-x.y.z (i.e. actual version number)
- The URL is http://box/elgg

Parameters
----------

Please review vars/main.yml as the installation parameters have
some constraints.

Users and Passwords
-------------------

There are a number of seemingly similar usernames and passwords in this installation:

* dbuser - the MySQL user that Elgg uses to access the database
           This is a local variable, the name of which corresponds to that in /opt/elgg/elgg-config/settings.php

* dbpassword - password for dbuser
               This is also a local variable, the name of which corresponds to that in /opt/elgg/elgg-config/settings.php

* elgg_mysql_password - this is the global name for dbpassword in default_vars.yml

* elgg_admin_user - the Elgg (not MySQL) user that is the administrator

* elgg_admin_password - the password for elgg_admin_user

More Tips & Tricks
------------------

If you're online, please see "Elgg Administration: What tips & tricks exist?" at: http://FAQ.IIAB.IO

If you're offline, Internet-in-a-Box's FAQ (Frequently Asked Questions) is here: http://box/info
