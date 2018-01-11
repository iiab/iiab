#!/bin/bash
# put initialization that needs to happen at every startup for IIAB here

if [ ! -f /etc/iiab/uuid ]; then
   uuidgen > /etc/iiab/uuid
fi

# Temporary promiscuous-mode workaround for RPi's WiFi "10SEC disease"
# Set wlan0 to promiscuous on boot if needed as gateway (i.e. AP's OFF)
# Scripts iiab-hotspot-on + iiab-hotspot-off SHOULD toggle this boot flag!
# https://github.com/iiab/iiab/issues/638#issuecomment-355455454
if [[ $(grep -i raspbian /etc/*release) &&
         ($(grep "hostapd_enabled = False" /etc/iiab/config_vars.yml) ||
             ((! $(grep "hostapd_enabled = True" /etc/iiab/config_vars.yml)) &&
                 $(grep "hostapd_enabled = False" /etc/iiab/iiab.ini)
             )
         )
   ]];
then
    ip link set dev wlan0 promisc on
fi

exit 0
