Please read "What is Ansible and what version should I use?" at [http://FAQ.IIAB.IO](http://FAQ.IIAB.IO)

Read https://github.com/iiab/iiab/wiki/IIAB-Contributors-Guide#ansible to learn more about how IIAB uses Ansible.

Starting in November 2019, IIAB's Ansible installer ([/opt/iiab/iiab/scripts/ansible](https://github.com/iiab/iiab/blob/master/scripts/ansible)) began installing these python3-* apt packages, in support of the following Ansible modules:

1. Ansible module: [pip](https://docs.ansible.com/ansible/latest/modules/pip_module.html)

   IIAB installs apt packages:
   - **python3-pip** (for IIAB's [Admin Console](https://github.com/iiab/iiab-admin-console))
   - **python3-setuptools**
   - **virtualenv** (is Python 3 only, for [roles/kalite](https://github.com/iiab/iiab/tree/master/roles/kalite) & [roles/calibre-web](https://github.com/iiab/iiab/tree/master/roles/calibre-web) ?) and pulls in additional packages... (`apt show virtualenv` shows "Depends: python3, python3-virtualenv")
      - **python3-virtualenv** and pulls in additional package... (`apt show python3-virtualenv` shows "Depends: python-pip-whl (>= 8.1.1-2), python3, python3-distutils, python3-pkg-resources") 
         - **python3-distutils**
   - **python3-venv** for Good Measure?

2. Ansible modules: [mysql_db](https://docs.ansible.com/ansible/latest/modules/mysql_db_module.html) and [mysql_user](https://docs.ansible.com/ansible/latest/modules/mysql_user_module.html) (for [roles/mysql](https://github.com/iiab/iiab/tree/master/roles/mysql))

   IIAB installs apt package:
   - **python3-pymysql** (see sudo's password-changing failure [iiab/iiab#1714](https://github.com/iiab/iiab/issues/1714) and [ansible/ansible#47736](https://github.com/ansible/ansible/issues/47736))

3. Ansible modules: [postgresql_db](https://docs.ansible.com/ansible/latest/modules/postgresql_db_module.html) and [postgresql_dbuser](https://docs.ansible.com/ansible/latest/modules/postgresql_user_module.html)

   IIAB installs apt package:
   - **python3-psycopg2** (for [roles/moodle](https://github.com/iiab/iiab/tree/master/roles/moodle))

4. Ansible module: [htpasswd](https://docs.ansible.com/ansible/latest/modules/htpasswd_module.html)

   IIAB installs apt package:
   - **python3-passlib** (for [roles/munin](https://github.com/iiab/iiab/tree/master/roles/munin))
