#!/bin/bash

# /usr/libexec/iiab-startup.sh is AUTOEXEC.BAT for IIAB
# (put initializations here, if needed on every boot)

if [ ! -f /etc/iiab/uuid ]; then
    uuidgen > /etc/iiab/uuid
    echo "/etc/iiab/uuid was MISSING, so a new one was generated."
fi

if [[ $(grep -i raspbian /etc/*release) != "" ]]; then  
   if [[ $(grep "^HOTSPOT=on" /etc/iiab/iiab.env) != "" ]]; then

      # need to find out which channel is used upstream
      wpa_supplicant -iwlan0 -c/etc/wpa_supplicant/wpa_supplicant.conf &
      sleep 3
      CHANNEL=`iw wlan0 info|grep channel|cut -d' ' -f2`
      echo $CHANNEL
      /usr/bin/killall wpa_supplicant
      /sbin/iw dev wlan0 interface add wlan0_ap type __ap

      # need unique MAC, so change mfg field, and pick 3 arbitrary octets
      /sbin/ip link set wlan0 address b8:27:99:12:34:56
      /sbin/ifup wlan0_ap
      /bin/systemctl restart dnsmasq.service

      # get the channel that is in use -- supplied by upstream wifi
      if [ ! -z "$CHANNEL" ]; then
         sed -i -e "s/^channel.*/channel=$CHANNEL /" /etc/hostapd/hostapd.conf
      fi
      systemctl start hostapd.service
      #sleep 5
      if [[ $(grep "^hostapd_enabled=True" /etc/iiab/iiab.env) ]]; then
         ip link set dev wlan0 promisc on
      fi
   fi

fi

# the following dummy function is a quick way to comment out bash code

function dummy {  #set promisc on for upstream on rpi - see above
# Temporary promiscuous-mode workaround for RPi's WiFi "10SEC disease"
# Sets wlan0 to promiscuous on boot if needed as gateway (i.e. AP's OFF).
# Manually run iiab-hotspot-[on|off] to toggle AP & boot flag hostapd_enabled
# https://github.com/iiab/iiab/issues/638#issuecomment-355455454
if [[ $(grep -i raspbian /etc/*release) &&
        #($(grep "hostapd_enabled = False" /etc/iiab/config_vars.yml) ||
            #((! $(grep "hostapd_enabled = True" /etc/iiab/config_vars.yml)) &&
                 ! $(grep "^hostapd_enabled = True" /etc/iiab/iiab.ini) ]];
                 # NEGATED LOGIC HELPS FORCE PROMISCUOUS MODE EARLY IN INSTALL
                 # (when computed_network.yml has not yet populated iiab.ini)

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
    ip link set dev wlan0 promisc on
    echo "wlan0 promiscuous mode ON, internal AP OFF: github.com/iiab/iiab/issues/638"
fi
}

exit 0
