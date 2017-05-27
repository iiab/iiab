#!/bin/bash
# start the vnc server and websockify server
/etc/init.d/vnc start

# if a parameter was passed it is the remote  addr
if [ $# -eq 1 ]; then
   iptables -I INPUT -p tcp -s $1 --dport 6080 -j ACCEPT
else
   # open the new port for direct access to the websocket
   iptables -I INPUT -p tcp --dport 6080 -j ACCEPT
fi

# launch the websocket server
systemctl start websockify.service
