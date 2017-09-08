============
xovis README
============

For information on the xovis feature see https://github.com/martasd/xovis/blob/master/README.md.

Links to Services
-----------------

To change the installation parameters edit vars/default_vars.yml:

xovis_target_host: "127.0.0.1:5984"
xovis_deployment_name: olpc

xovis_db_name: xovis
xovis_db_user: admin
xovis_db_password: admin
xovis_db_login: "{{ xovis_db_user }}:{{ xovis_db_password }}"
xovis_db_url: "http://{{ xovis_db_login }}@{{ xovis_target_host }}/{{ xovis_db_name }}"

xovis_root: "/opt/xovis"
xovis_backup_dir: "/library/users"
xovis_repo_url: "https://github.com/martasd/xovis.git"
xovis_chart_heading: "My School: Usage Data Visualization"

Most of these will not need changing, but you will likely want to change the deployment name, the chart heading, and the database admin password.
