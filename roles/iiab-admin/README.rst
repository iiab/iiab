.. |ss| raw:: html

   <strike>

.. |se| raw:: html

   </strike>

.. |nbsp| unicode:: 0xA0
   :trim:

=================
iiab-admin README
=================

`Internet-in-a-Box <https://internet-in-a-box.org>`_ (IIAB) encourages you to pay attention to the security of your learning community.

This Ansible playbook is one of the very first that runs when you install IIAB, and we hope reading this helps you understand your choices:

Configure user 'iiab-admin'
---------------------------

* `admin-user.yml <tasks/admin-user.yml>`_ configures a Linux user that will give you access to IIAB's Admin Console (http://box.lan/admin) after IIAB is installed — and can also help you at the command-line with IIAB community support commands like {iiab-diagnostics, iiab-hotspot-on, iiab-check-firmware, etc}.
   * **IIAB does not set or generate the password.**  The account and password are expected to exist before IIAB runs: use the OS installer, Raspberry Pi Imager, cloud-init, or run **passwd** yourself.  This keeps the credential under the operator's control and avoids a password that is known to anyone who reads the source.
   * If the account does not exist, IIAB creates it locked (no password) and adds it to the Admin Console group.  Set a password with **sudo passwd iiab-admin** before logging in.
   * Existing accounts are reused as-is.  IIAB only adds the Admin Console group membership; it does not change the password or shell.
* By default this is the account that ran **sudo iiab** (``SUDO_USER``), falling back to the current user.  That reuses the operator's existing OS account and password instead of creating a separate ``iiab-admin`` login.  If you prefer a dedicated account such as ``iiab-admin``, ``pi``, or ``ubuntu``, set ``iiab_admin_user`` in your `/etc/iiab/local_vars.yml <https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it%3F>`_ (preferably before installing IIAB!).
   * You can set ``iiab_admin_user_install: False`` if you're sure you know how to do all this `account configuration <tasks/admin-user.yml>`_ manually.

Sudo and support commands
-------------------------

* The admin user is **not** added to the ``sudo`` group by default.  General root access is opt-in with ``iiab_admin_can_sudo: True``.
* IIAB's own support commands are covered by a narrow sudoers file, ``/etc/sudoers.d/iiab-support``.  It grants the ``iiab-admin`` group only the commands in ``iiab_admin_support_commands`` (``iiab-diagnostics``, ``iiab-check-firmware``, ``iiab-hotspot-on``, ``iiab-hotspot-off``, ``iiab-internet-on``, ``iiab-internet-off``, ``iiab-summary``, and ``iiab-network``).
   * Add or remove commands in ``/etc/iiab/local_vars.yml`` and re-run ``cd /opt/iiab/iiab`` followed by ``sudo ./runrole iiab-admin``.
   * Set ``iiab_admin_support_sudo: False`` to remove the file entirely.
* Upgrades do not remove an existing user from the ``sudo`` group, because that would break installs that rely on it.  Set ``iiab_admin_revoke_sudo: True`` if you want to remove it deliberately.
* A command that can run arbitrary playbooks or open a shell (for example ``iiab-update``) is intentionally **not** in the scoped list.  Give the account full sudo if you need that.

Security
--------

* A user MUST be a member of at least one of these 2 Linux groups, in order to log in to IIAB's Admin Console: (http://box.lan/admin)
   #. ``iiab-admin`` (specified by ``admin_console_group`` in `/opt/iiab/iiab/vars/default_vars.yml <../../vars/default_vars.yml>`_ and `/opt/iiab/iiab-admin-console/vars/default_vars.yml <https://github.com/iiab/iiab-admin-console/blob/master/vars/default_vars.yml>`_)
   #. ``sudo``
* By default IIAB adds the invoking operator (``SUDO_USER``) to ``iiab-admin``, so the Console login uses the same OS account and password the operator already has.  The Console does not check the ``wheel`` group.
* Please read much more about what escalated (root) actions are authorized when you log into IIAB's Admin Console, and how this works: https://github.com/iiab/iiab-admin-console/blob/master/Authentication.md
* Root SSH login is not enabled by IIAB.  ``iiab-root-login`` is an explicit, separately invoked opt-in for installs that need it; see that script's warning before using it.
* If your IIAB includes Tailscale (VPN), ``/root/.ssh/authorized_keys`` should be installed by `roles/tailscale/tasks/install.yml <../tailscale/tasks/install.yml>`_ to facilitate remote community support.  Feel free to remove this as mentioned here: https://wiki.iiab.io/go/Security
* Upgrade warnings for the old published password are implemented in `/etc/profile.d/iiab-pwdwarn-profile.sh <templates/iiab-pwdwarn-profile.sh.j2>`_.  New accounts do not use that password.

Example
=======

* If you later change your mind about ``sudo`` privileges for user 'iiab-admin' (as specified by ``iiab_admin_user``) then do this:
   #. Go ahead and change the value of ``iiab_admin_can_sudo`` (to either True or False) in `/etc/iiab/local_vars.yml <https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it%3F>`_
   #. Make sure that ``iiab_admin_user_install: True`` is also set.
   #. Then re-run this Ansible playbook, by running ``cd /opt/iiab/iiab`` followed by ``sudo ./runrole --reinstall iiab-admin``
   #. If you also want to remove an existing ``sudo`` membership, set ``iiab_admin_revoke_sudo: True`` for that run.

Historical Notes
================

* Before October 2026, ``iiab-admin`` was added to the ``sudo`` group by default and IIAB set new accounts to the published password ``g0adm1n``.  Both defaults have been retired: IIAB no longer sets a password at all, and the string remains only so upgrades can warn about accounts that still use it (``iiab_admin_legacy_pwd``).
* We no longer support setting your password using a hash e.g. ``python -c 'import crypt; print crypt.crypt("<plaintext>", "$6$<salt>")'`` (or the Python < 3.13 equivalent, ``python3 -c 'import crypt; print(crypt.crypt("<plaintext>", crypt.mksalt(crypt.METHOD_SHA512)))'`` or the CLI equivalent, ``openssl passwd -6 -salt $(openssl rand -base64 12) "plaintext"``) as these are very cumbersome — and worse, exposing your "salt" opens up your password to `possible attack <https://stackoverflow.com/questions/6776050/how-long-to-brute-force-a-salted-sha-512-hash-salt-provided>`_.  [October 2020]
* The sudo flag ``NOPASSWORD:`` and the ``wheel`` group are similarly no longer recommended, so that your IIAB faces fewer security risks.  [October 2020]

Remote Support Tools
--------------------

The `iiab-diagnostics <../../scripts/iiab-diagnostics.README.md>`_ and `Tailscale (VPN) <https://en.wikipedia.org/wiki/Tailscale>`_ options mentioned above can greatly help you empower your community, typically during the implementation phase of your project, even if Linux is new to you.

Similarly, `tasks/main.yml <tasks/main.yml>`_ adds a couple text mode tools — extremely helpful over expensive / low-bandwidth connections:

* `lynx <https://en.wikipedia.org/wiki/Lynx_(web_browser)>`_
* `screen <https://linuxize.com/post/how-to-use-linux-screen/>`_

*More great tools to help you jumpstart community action at a distance:*

* `FAQ.IIAB.IO <https://wiki.iiab.io/go/FAQ>`_ > "How can I remotely manage my Internet-in-a-Box?"

Admin Console
-------------

Has been moved to this separate git repo: https://github.com/iiab/iiab-admin-console
