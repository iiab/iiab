#!/bin/bash

if [ -f /.fw_replaced ]; then
    echo -e "\n \e[41;1mWiFi Firmware has been replaced, per iiab/iiab#823.\e[0m"
    if grep -q '^wifi_hotspot_capacity_rpi_fix:\s\+[fF]alse\b' /etc/iiab/local_vars.yml ; then
        echo -e " \e[100;1mIf you want these warnings to stop, run:\e[0m"
        echo
        echo -e " \e[100;1msudo rm /.fw_replaced\e[0m\n"
    else
        echo -e " \e[41;1mReboot is required to activate.\e[0m\n"
    fi
fi
