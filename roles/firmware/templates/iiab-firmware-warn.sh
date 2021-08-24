#!/bin/bash

if [ -f /.fw_replaced ]; then
    echo -e "\n \033[31;5mWiFi Firmware has been replaced, per iiab/iiab#823.\033[0m"
    if grep -q '^wifi_hotspot_capacity_rpi_fix:\s\+[fF]alse\b' /etc/iiab/local_vars.yml ; then
        echo -e " \033[31;5mRun 'sudo rm /.fw_replaced' if you want these warnings to stop.\033[0m\n"
    else
        echo -e " \033[31;5mReboot is required to activate.\033[0m\n"
    fi
fi
