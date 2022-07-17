#!/bin/bash
if ! [ -f /etc/iiab/install-flags/iiab-network-complete ]; then
    zenity --question --width=200 --text="You need to provision the network. Ensure you have your upstream internet active first. You might be prompted for your password. Should you not want to provision the network at this time just click NO"
    rc=$?
    if [ $rc == "1" ]; then
        exit 0
    fi
    x-terminal-emulator -e /usr/local/bin/iiab-network
    rc=$?
    if [ $rc == "1" ]; then
        zenity --question --width=200 --text="Network exited with error, please review /opt/iiab/iiab/iiab-network.log"
        exit 1
    fi
    zenity --question --width=200 --text="A REBOOT is recommended, would you like to REBOOT now?"
    rc=$?
    if [ $rc == "1" ]; then
        exit 0
    fi
    x-terminal-emulator -e /usr/sbin/reboot
fi
