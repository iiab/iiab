#!/bin/bash

if [ -f /tmp/.fw_modified ]; then
    echo -e "\n\e[41;1mWiFi Firmware link(s) modified, per iiab/iiab#2853: PLEASE REBOOT!\e[0m"
    # /tmp should be auto cleaned with a reboot
    #echo
    #echo -e "If you want this warning to stop, run: sudo rm /tmp/.fw_modified\n"
fi

# \e[1m = bright white    \e[100;1m = bright white, on gray    \n\e[41;1m = bright white, on red
