===========
ELGG README
===========

Elgg is an award-winning social networking engine, delivering the building blocks
that enable businesses, schools, universities and associations to create their own
fully-featured social networks and applications.

http://elgg.org/

After Installation
------------------

Go to http://box.lan/elgg and log on as Admin with password changeme.

Change the following:

* Administrator password

* Title to appear on elgg screens and any other settings as desired.

Locations
---------

- The uploaded files are expected to be in /library/elgg
- The URL is /elgg

Parameters
----------

Please review vars/main.yml as the installation parameters have
some constraints.

Users and Passwords
-------------------

There are a number of seemilingly similar user names and passwords in this installation:

* dbuser - the mysql user that elgg uses to access the database.  This is a local variable
           the name of which corresponds to that in the elgg settings.php file.

* dbpassword - password for dbuser. This is also a local variable
               the name of which corresponds to that in the elgg settings.php file.

* elgg_mysql_password - this is the global name for dbpassword in default_vars.yml.

* elgg_admin_user - the elgg (not mysql) user that is the administrator.

* elgg_admin_password - the password for elgg_admin_user.
