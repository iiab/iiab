#!/bin/bash

# SEE ALSO: /etc/xdg/lxsession/LXDE-pi/sshpwd-lxde-iiab.sh sourced from...
# https://github.com/iiab/iiab/blob/master/roles/iiab-admin/templates/sshpwd-lxde-iiab.sh
# ...invoked by /etc/xdg/lxsession/LXDE-pi/autostart which is customized by...
# https://github.com/iiab/iiab/blob/master/roles/iiab-admin/tasks/main.yml#L32-L36

# For Localization/Translation: (use /usr/bin/gettext below if later nec!)
#export TEXTDOMAIN=Linux-PAM
#. gettext.sh
# https://github.com/raspberrypi-ui/pam/blob/master/etc/profile.d/sshpwd.sh
# https://github.com/raspberrypi-ui/pprompt/blob/master/sshpwd.sh

# bash syntax "function check_user_pwd() {" was removed, as it prevented all
# lightdm/graphical logins (incl autologin) on Raspbian: #1252 -> PR #1253
check_user_pwd() {
    #[ $(id -un) = "root" ] || return 2
    #[ $(id -un) = "root" ] || [ $(id -un) = "iiab-admin" ] || return 2
    [ -r /etc/shadow ] || return 2    # FORCE ERROR if /etc/shadow not readable
    # *BUT* overall bash script still returns exit code 0 ("success").

    #id -u $1 > /dev/null 2>&1 || return 2    # Not needed if return 1 is good
    # enough when user does not exist.  Or uncomment to FORCE ERROR CODE 2.
    # Either way, overall bash script still returns exit code 0 ("success").

    # $meth (hashing method) is typically '6' which implies 5000 rounds
    # of SHA-512 per /etc/login.defs -> /etc/pam.d/common-password
    meth=$(grep "^$1:" /etc/shadow | cut -d: -f2 | cut -d$ -f2)
    salt=$(grep "^$1:" /etc/shadow | cut -d: -f2 | cut -d$ -f3)
    hash=$(grep "^$1:" /etc/shadow | cut -d: -f2 | cut -d$ -f4)
    [ $(python3 -c "import crypt; print(crypt.crypt('$2', '\$$meth\$$salt'))") == "\$$meth\$$salt\$$hash" ]
}

# 2020-10-13 https://github.com/iiab/iiab/issues/2561 RECAP: Above was blocking
# logins, lacking permissions to grep /etc/shadow.  As it's unreasonable to
# provide sudo privs to every user (with "NOPASSWD:" password-free sudo access
# or not, as required by graphical logins!)

# MORE DETAILS: most logins (graphical or tty) blocked on above [sudo] grep
# (at least tty logins finally let sudoers in, after entering password twice!)
# EXCEPTION: ALL GRAPHICAL logins to Raspberry Pi OS still worked, no matter
# whether sshpwd-lxde-iiab.sh's "sudo grep" displayed our popup warning or not!

# HISTORICAL: if password-free sudo access is truly nec, it can be set with
# "iiab-admin ALL=(ALL) NOPASSWD: ALL" in /etc/sudoers as seen in the older:
# https://github.com/iiab/iiab/blob/master/roles/iiab-admin/tasks/admin-user.yml

if check_user_pwd "{{ iiab_admin_user }}" "{{ iiab_admin_published_pwd }}" ; then    # iiab-admin g0adm1n
    echo
    echo "Published password in use by user '{{ iiab_admin_user }}'."
    echo "THIS IS A SECURITY RISK - please run 'sudo passwd {{ iiab_admin_user }}' to change it."
    echo
fi
