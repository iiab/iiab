#!/bin/bash

if [ -f /tmp/.fw_modified ]; then
    echo -e "\n\e[41;1mWiFi Firmware link(s) modified, per iiab/iiab#2853: PLEASE REBOOT!\e[0m"
    echo
    echo -e "If you want this warning to stop, reboot to remove /tmp/.fw_modified\n"
fi

# \e[1m = bright white    \e[100;1m = bright white, on gray    \n\e[41;1m = bright white, on red
