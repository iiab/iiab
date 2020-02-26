#!/bin/bash

# /usr/libexec/iiab-startup.sh is AUTOEXEC.BAT for IIAB
# (put initializations here, if needed on every boot)

if [ ! -f /etc/iiab/uuid ]; then
    uuidgen > /etc/iiab/uuid
    echo "/etc/iiab/uuid was MISSING, so a new one was generated."
fi

# Temporary promiscuous-mode workaround for RPi's WiFi "10SEC disease"
# Sets wlan0 to promiscuous on boot if needed as gateway (i.e. AP's OFF).
# Manually run iiab-hotspot-[on|off] to toggle AP & boot flag hostapd_enabled
# https://github.com/iiab/iiab/issues/638#issuecomment-355455454
if [[ $(grep -i raspbian /etc/*release) &&
        #($(grep "hostapd_enabled = False" /etc/iiab/config_vars.yml) ||
            #((! $(grep "hostapd_enabled = True" /etc/iiab/config_vars.yml)) &&
                 ! $(grep "^HOSTAPD_ENABLED=True" {{ iiab_env_file }}) ]];
                 # NEGATED LOGIC HELPS FORCE PROMISCUOUS MODE EARLY IN INSTALL
                 # (when network/tasks/main.yml hasn't yet populated iiab.env)

                 # RESULT: WiFi-installed IIAB should have wlan0 properly in
                 # promiscuous mode Even On Reboots (if 2-common completed!)

                 # CAUTION: roles/network/tasks/main.yml (e.g. if you run
                 # ./iiab-network, "./runtags network", or ./iiab-install)
                 # can toggle your hostapd_enabled setting if it detects a
                 # different "primary gateway" (eth0 vs. wlan0 vs. none) to the
                 # Internet -- even if you have not run iiab-hotspot-on|off !
            #)
        #)
   #]];
then
#    ip link set dev wlan0 promisc on
    echo "wlan0 promiscuous mode ON, internal AP OFF: github.com/iiab/iiab/issues/638 DISABLED"
fi

exit 0
