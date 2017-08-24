#!/bin/bash 
# credit to the folks at raspberry pi foundatioon
check_hash ()
{
   if ! id -u iiab-admin > /dev/null 2>&1 ; then return 0 ; fi
   if grep -q "^PasswordAuthentication\s*no" /etc/ssh/sshd_config ; then return 0 ; fi
   SHADOW="$(sudo -n grep -E '^iiab-admin:' /etc/shadow 2>/dev/null)"
   test -n "${SHADOW}" || return 0
   if echo $SHADOW | grep -q "iiab-admin:!" ; then return 0 ; fi
   SHADOW_PW=$(echo $SHADOW | cut -d: -f2)
   if [ "$SHADOW_PW" != '{{ iiab_admin_passw_hash }}' ]; then return 0 ; fi

		echo
		echo "SSH is enabled and the default password for the 'iiab-admin' user is unchanged."
		echo "This is a security risk - please login as the 'iiab-admin' user and type 'passwd' to change password."
		echo
}

systemctl is-active {{ sshd_service }} > /dev/null && check_hash
unset check_hash
