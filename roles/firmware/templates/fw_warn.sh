#!/bin/bash
if [ -f /.fw_replaced ]; then
    echo -e " \033[31;5mFirmware has been replaced\033[0m"
    echo -e " \033[31;5mReboot is required to activate\033[0m"
fi

