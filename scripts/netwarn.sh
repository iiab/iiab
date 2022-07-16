if ! [ -f /etc/iiab/install-flags/iiab-network-complete ]; then
    zenity --question --text="You need to provision the network. Ensure you have your upstream internet active first if needed. You will be prompted for your password. You should REBOOT afterwards, do you want to Proceed?"
    rc=$?
    if [ $rc == "1" ]; then
        exit 1
    fi
    x-terminal-emulator -e /usr/local/bin/iiab-network
fi
