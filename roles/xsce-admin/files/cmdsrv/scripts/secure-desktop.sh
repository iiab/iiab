#!/bin/bash
# close down the vnc remote desktop

# delete any rules permitting 6080
iptables -L INPUT |grep 6080
while [ $? -eq 0 ];do
  iptables -D INPUT 1
  iptables -L INPUT  |grep 6080
done

/etc/init.d/vnc stop
systemctl stop websockify.service
iptables -D INPUT -p tcp --dport 6080 -j ACCEPT
