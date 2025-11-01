#!/bin/bash

if [ "$IFACE" == "br1" ]; then
    /bin/systemctl --no-block start dnsmasq.service
    echo "br1 Started dnsmasq"
fi
