#!/bin/bash

function check_user_pwd() {
    # $meth (hashing method) is typically '6' which implies 5000 rounds
    # of SHA-512 per /etc/login.defs -> /etc/pam.d/common-password
    meth=$(sudo grep "^$1:" /etc/shadow | cut -d: -f2 | cut -d$ -f2)
    salt=$(sudo grep "^$1:" /etc/shadow | cut -d: -f2 | cut -d$ -f3)
    hash=$(sudo grep "^$1:" /etc/shadow | cut -d: -f2 | cut -d$ -f4)
    [ $(python3 -c "import crypt; print(crypt.crypt('$2', '\$$meth\$$salt'))") == "\$$meth\$$salt\$$hash" ]
}

# credit to the folks at raspberry pi foundatioon
check_hash () {
    if ! id -u iiab-admin > /dev/null 2>&1 ; then return 0 ; fi
    if grep -q "^PasswordAuthentication\s*no" /etc/ssh/sshd_config ; then return 0 ; fi
    #SHADOW="$(sudo -n grep -E '^iiab-admin:' /etc/shadow 2>/dev/null)"
    #test -n "${SHADOW}" || return 0
    #if echo $SHADOW | grep -q "iiab-admin:!" ; then return 0 ; fi
    #SHADOW_PW=$(echo $SHADOW | cut -d: -f2)
    #if [ "$SHADOW_PW" != '{{ iiab_admin_pwd_hash }}' ]; then return 0 ; fi
    if check_user_pwd "iiab-admin" "g0adm1n"; then
        echo -e "\nSSH is enabled and the default password for the 'iiab-admin' user is unchanged."
        echo -e "This is a security risk - please login as user 'iiab-admin' and run 'passwd' to change its password.\n"
    fi
}

systemctl is-active {{ sshd_service }} > /dev/null && check_hash
unset check_hash
