#!/bin/bash

. /etc/xsce/xsce.env

if [ "$OS" = "Debian" ] || [ "$OS" = "raspbian" ]; then
  /bin/sleep 3
  /sbin/shutdown -P now
else
  /usr/bin/sleep 3
  /usr/sbin/shutdown -P now
fi

exit 0
