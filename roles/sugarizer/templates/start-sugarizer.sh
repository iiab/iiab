#!/bin/bash
# shim to daemonize node sugarizer.js, declare log target, return 0
cd /opt/iiab/sugarizer-server
nohup /bin/node sugarizer.js >> /var/log/sugarizer.log &
exit 0
