#!/bin/bash

# SEE ALSO: /etc/xdg/lxsession/LXDE-pi/sshpwd-lxde-iiab.sh sourced from...
# https://github.com/iiab/iiab/blob/master/roles/iiab-admin/templates/sshpwd-lxde-iiab.sh
# ...invoked by /etc/xdg/lxsession/LXDE-pi/autostart which is customized by...
# https://github.com/iiab/iiab/blob/master/roles/iiab-admin/tasks/main.yml#L46-L50

# For Localisation:
#export TEXTDOMAIN=Linux-PAM
#. gettext.sh
# https://github.com/raspberrypi-ui/pam/blob/master/etc/profile.d/sshpwd.sh
# https://github.com/raspberrypi-ui/pprompt/blob/master/sshpwd.sh

# bash syntax "function check_user_pwd() {" was removed, as it prevented all
# lightdm/graphical logins (incl autologin) on Raspbian: #1252 -> PR #1253
check_user_pwd() {

    # 1. 'sudo su -' invokes this script as root:
    [ $(id -un) = "root" ] || return 1    # FORCE ERROR IF RUN BY NON-root
    # *BUT* overall bash script still returns exit code 0 ("success")
    # as needed by Ubuntu 20.04 graphical logins, etc!

    # 2. Graphical Logins invoke this script as the user logging in: (USELESSLY)
    #[ $(id -un) = "$1" ] || [ $(id -un) = "root" ] || return 1
    # SO FORMERLY: this could also be run by non-root accounts e.g. iiab-admin
    # if sudo access set with "%wheel ALL= NOPASSWD: ALL" in /etc/sudoers per
    # https://github.com/iiab/iiab/blob/master/roles/iiab-admin/tasks/admin-user.yml
    # BUT: warning popups did not result on most OS's, much as mentioned here:
    # https://github.com/iiab/iiab/blob/master/roles/iiab-admin/tasks/main.yml#L38-L44

    # $meth (hashing method) is typically '6' which implies 5000 rounds
    # of SHA-512 per /etc/login.defs -> /etc/pam.d/common-password
    meth=$(grep "^$1:" /etc/shadow | cut -d: -f2 | cut -d$ -f2)
    salt=$(grep "^$1:" /etc/shadow | cut -d: -f2 | cut -d$ -f3)
    hash=$(grep "^$1:" /etc/shadow | cut -d: -f2 | cut -d$ -f4)
    [ $(python3 -c "import crypt; print(crypt.crypt('$2', '\$$meth\$$salt'))") == "\$$meth\$$salt\$$hash" ]
}

if check_user_pwd "{{ iiab_admin_user }}" "g0adm1n"; then    # iiab-admin
    echo
    echo $(/usr/bin/gettext "The published password for user '{{ iiab_admin_user }}' is in use.")
    echo $(/usr/bin/gettext "THIS IS A SECURITY RISK - please run 'sudo passwd {{ iiab_admin_user }}' to change it.")
    echo
fi
