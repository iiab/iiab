#!/bin/bash 
# credit to the folks at raspberry pi foundatioon
check_hash ()
{
   if ! id -u xsce-admin > /dev/null 2>&1 ; then return 0 ; fi
   if grep -q "^PasswordAuthentication\s*no" /etc/ssh/sshd_config ; then return 0 ; fi
   test -x /usr/bin/mkpasswd || return 0
   SHADOW="$(sudo -n grep -E '^xsce-admin:' /etc/shadow 2>/dev/null)"
   test -n "${SHADOW}" || return 0
   if echo $SHADOW | grep -q "xsce-admin:!" ; then return 0 ; fi
   SHADOW_PW=$(echo $SHADOW | cut -d: -f2)
   if [ "$SHADOW_PW" != "\$6\$xsce51\$D.IrrEeLBYIuJkGDmi27pZUGOwPFp98qpl3hxMwWV4hXigFGmdSvy3s/j7tn6OnyTTLmlV7SsN0lCUAFzxSop." ]; then return 0 ; fi

   if echo "${SHADOW}" | grep -q "${HASH}"; then
	zenity --warning --text="SSH is enabled and the default password for the 'xsce-admin' user has not been changed.\nThis is a security risk - please go to the xsce-console and use utilities-> change password   to set a new password."
   fi
}

if service ssh status | grep -q running; then
	check_hash
fi
unset check_hash
