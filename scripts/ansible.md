In order to use optional modules that ansible is capable of the libraries
need to be installed, we make use of the following ansible modules:

1. pip: we install python3-pip python3-setuptools virtualenv
   as per https://docs.ansible.com/ansible/latest/modules/pip_module.html
   virtualenv is python3 only and pulls in python3-distutils python3-virtualenv
   `apt show virtualenv` Depends: python3, python3-virtualenv
   `apt show python3-virtualenv` Depends: python-pip-whl (>= 8.1.1-2), python3, python3-distutils, python3-pkg-resources

2. mysql_db: python3-pymysql
   https://docs.ansible.com/ansible/latest/modules/mysql_db_module.html#mysql-db-module

3. mysql_user: python3-pymysql
   https://docs.ansible.com/ansible/latest/modules/mysql_user_module.html#mysql-user-module
   https://github.com/ansible/ansible/issues/47736

4. postgresql_db: python3-psycopg2
   https://docs.ansible.com/ansible/latest/modules/postgresql_db_module.html#postgresql-db-module

5. postgresql_dbuser: python3-psycopg2
   https://docs.ansible.com/ansible/latest/modules/postgresql_user_module.html#postgresql-user-module

6. htpasswd: python3-passlib
   https://docs.ansible.com/ansible/latest/modules/htpasswd_module.html?highlight=htpasswd
