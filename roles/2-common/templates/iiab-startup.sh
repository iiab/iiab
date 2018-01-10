#!/bin/bash
# put initialization that needs to happen at every startup for IIAB here

if [ ! -f /etc/iiab/uuid ]; then
   uuidgen > /etc/iiab/uuid
fi

# Experimental/Temporary workaround for WiFi "10SEC disease"
# https://github.com/iiab/iiab/issues/638#issuecomment-355455454
if grep -qi raspbian /etc/*release; then ip link set dev wlan0 promisc on; fi

exit 0
