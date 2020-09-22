#!/bin/bash

if [ -f /.fw_replaced ]; then
    echo -e "\n \033[31;5mWiFi Firmware has been replaced, per iiab/iiab#823.\033[0m"
    echo -e " \033[31;5mReboot is required to activate.\033[0m\n"
fi
