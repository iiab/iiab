#!/bin/bash
# put initialization that needs to happen at every startup for IIAB here

if [ ! -f /etc/iiab/uuid ]; then
   uuidgen > /etc/iiab/uuid
fi

# Temporary promiscuous-mode workaround for WiFi "10SEC disease"
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
