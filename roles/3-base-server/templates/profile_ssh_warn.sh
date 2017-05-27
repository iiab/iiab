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

		echo
		echo "SSH is enabled and the default password for the 'xsce-admin' user is unchanged."
		echo "This is a security risk - please login as the 'xsce-admin' user and type 'passwd' to change password."
		echo
}

if /usr/sbin/service ssh status | grep -q running; then
	check_hash
fi
unset check_hash
