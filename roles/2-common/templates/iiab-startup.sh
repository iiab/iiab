#!/bin/bash
# put initialization that needs to happen at every startup for IIAB here

if [ ! -f /etc/iiab/uuid ]; then
   uuidgen > /etc/iiab/uuid
fi

# Experimental/Temporary WiFi workaround:
# https://github.com/iiab/iiab/issues/638#issuecomment-355455454
ip link set dev wlan0 promisc on

exit 0
