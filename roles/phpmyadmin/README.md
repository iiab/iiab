## Authentication for phpMyAdmin via MySQL

#### Overview
[phpMyAdmin](https://www.phpmyadmin.net/) is a PHP interface to MySQL tables. It permits a browser client to inspect and modify a MySQL database across a network. It permits a Graphical User interface to achieve almost the same level of control as can be achieved via ssh and the command-line tool "mysql". But for most users, who do not use the (text-based) command-line interface regularly, phpMyAdmin is much easier to learn and remember.

#### Access to MySQL tables all descends from "root".
1. When MySQL is installed, it is prepared to create its own set of users and passwords that is distinct from the usernames and passwords that is maintained by the operating system. Initially the only user permitted to add or change users is a user named "root" who is already signed on (and therefore knows the Linux root password). The normal path for  person setting up a MySQL database is to use the "mysql" command line tool to create new users and assign passwords. 
2. phpMyAdmin, because it is a browser-based HTML PHP application, is limited in what it can do, and what it can access — until the "root" user creates users and access privileges, as mentioned above. (HTML servers always run with very low privileges)

#### Installing phpMyAdmin
1. First, a user will need to set `phpmyadmin_install: True` and `phpmyadmin_enabled: True` in [/etc/iiab/local_vars.yml](http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F)
2. Then install IIAB.  Or if IIAB is already installed, run:
   ```
   cd /opt/iiab/iiab
   sudo ./runrole phpmyadmin
   ```

#### Testing phpMyAdmin
1. It is possible to quickly test your phpMyAdmin installation. 
3. There is a small table already created in your MySQL databaase by the Admin Console called `iiab_feedback`
4. A small script can be run, that creates user "Admin" with password "changeme" and has access to this table only:
   ```
   sudo mysql < /opt/iiab/iiab/roles/phpmyadmin/templates/mkuser
   ```
5. Finally, test that it's working by browsing to http://box.lan/phpyadmin with username `Admin` and password `changeme`
