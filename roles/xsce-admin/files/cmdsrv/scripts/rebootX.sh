#!/bin/bash

. /etc/xsce/xsce.env

if [ "$OS" = "Debian" ] || [ "$OS" = "raspbian" ]; then
	/bin/sleep 3
	/sbin/reboot
else
	/usr/bin/sleep 3
	/usr/sbin/reboot
fi
exit 0
