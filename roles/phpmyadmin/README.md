## Authentication for Phpmyadmin via MySQL
#### Overview
Phpmyadmin is a php interface to MySQL tables. It permits a browser client to inspect and modify a MySQL database across a network. It permits a Graphical User interface to achieve almost the same level of control as can be achieed via ssh and the commandline tool "mysql". But for most users, who do not use the text based commandline interface regularly, phpmyadmin is much easier to learn and remember.

#### Access to MySQL tables all descends from "root".
1. When MySQL is installed, it is prepared to create it's own set of users and passwords that is distinct from the usernames and passwords that is maintained by the operating system. Initially the only user permitted to add or change users is a user named "root" who is already signed on (and therefore knows the linux root password). The normal path for  person setting up a MySQL database is to use the "mysql" command line tool to create new users and assign passwords. 

1. Phpmyadmin, because it is a browser based HTML php applications, is limited in what it can do, and what it can access, until the "root" user creates users and access privileges, as mentioned above. (HTML servers always run with very low privileges).

#### Installing Phpmyadmin
1. First, a user will need to set phpmyadmin_install: True and phpmyadmin_enabled: True in /etc/iiab/local_vars.yml.
2. Then run 
```
     cd /opt/iiab/iiab
     ./runrole phpmyadmin
```
#### Testing Phpmyadmin

1. It is possible to quickly test your phpmyadmin installation. 
3. There is a small table already created in your MySQL databaase by the Admin Console called iiab_feedbck.
4. A small script creates a user "Admin" with a password "changeme" that has acccess only to this table which can be run:
```
    sudo mysql < /opt/iiab/iiab/roles/phpmyadmin/templates/mkuser
```
5. Test by browsig to http://box.lan/phpyadmin and entering the credentials username: Admin  password: changeme
