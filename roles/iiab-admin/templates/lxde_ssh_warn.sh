#!/bin/bash

check_user_pwd () {
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
   #test -x /usr/bin/mkpasswd || return 0
   #SHADOW="$(sudo -n grep -E '^iiab-admin:' /etc/shadow 2>/dev/null)"
   #test -n "${SHADOW}" || return 0
   #if echo $SHADOW | grep -q "iiab-admin:!" ; then return 0 ; fi
   #SHADOW_PW=$(echo $SHADOW | cut -d: -f2)
   #if [ "$SHADOW_PW" != "\$6\$iiab51\$D.IrrEeLBYIuJkGDmi27pZUGOwPFp98qpl3hxMwWV4hXigFGmdSvy3s/j7tn6OnyTTLmlV7SsN0lCUAFzxSop." ]; then return 0 ; fi
   #if echo "${SHADOW}" | grep -q "${HASH}"; then
   if check_user_pwd "iiab-admin" "{{ iiab_admin_published_pwd }}"; then
       zenity --warning --text="SSH is enabled and the published password for user 'iiab-admin' is in use.\nTHIS IS A SECURITY RISK - please change its password using IIAB's Admin Console (http://box/admin) -> Utilities -> Change Password."
   fi
}

#if service ssh status | grep -q running; then
#    check_hash
#fi
systemctl is-active {{ sshd_service }} > /dev/null && check_hash
unset check_hash
