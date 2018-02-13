=====================
9-local-addons README
=====================

This 9th stage is a placeholder for server apps (roles, tasks or otherwise) that are locally developed -- or of an experimental nature.

As in the case of 6-generic-apps, 7-edu-apps, and 8-mgmt-tools: this stage is intended to install user-facing or operator-facing server apps.

Development
-----------

Consider creating your own Ansible role to add essential functionality to Internet-in-a-Box.  You can copy any role you find within /opt/iiab/iiab/roles, and build from there!

Packaging
---------

Add your Ansible role into /opt/iiab/iiab/roles/9-local-addons/tasks/main.yml

It will then get installed as part of the next Ansible run (e.g. "cd /opt/iiab/iiab" and then "./iiab-install --reinstall").

More Info
---------

Have a look at https://github.com/iiab/iiab/wiki/IIAB-Architecture (offline at http://box/info/IIAB-Architecture.html) for more detailed information.
