Samba README
============

Do you want your Internet-in-a-Box (IIAB) to act as a file server for your classroom or school?

If `Samba <https://www.samba.org/samba/docs/>`_ is installed and enabled as part of your IIAB's `/etc/iiab/local_vars.yml <https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F>`_, your IIAB server can advertise a shared "public" folder, available to Windows PC's and laptops on your network.

Default Permissions
-------------------

- Users may read and write to the "public" shared folder.
- They are forced to store their files as a user who has no ability to log on to the server.
- The user, with no ability to log on, has a password which is very difficult to guess e.g. ``verylong%and$hard^to@guess``

Security
--------

**It's critical you understand Samba security,** so as not to endanger your students and community:

- `https://en.wikipedia.org/wiki/Samba_(software)#Security <https://en.wikipedia.org/wiki/Samba_(software)#Security>`_
- https://ubuntu.com/server/docs/samba-securing

Please review the default `/etc/samba/smb.conf <templates/smb.conf.j2>`_ file, and revise it appropriately.

Please also review your overall `IIAB Security <http://wiki.laptop.org/go/IIAB/Security>`_.
