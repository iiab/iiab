#!/bin/sh
if [ -f /etc/iiab/install-flags/iiab-network-complete ]; then
    exit
fi

zenity --question --width=350 --text="IIAB needs to configure networking:\n\n► Internet must be live before you begin.\n►You might be prompted for your password.\n\nContinue?"
case $? in
    -1|5)
        exit 1
        ;;

    1)
        exit 0
        ;;

    0)
        x-terminal-emulator -e /usr/local/bin/iiab-network
        ;;
esac

if [ "$?" = "1" ]; then
    zenity --warning --width=350 --text="iiab-network exited with error.\n\nPlease review /opt/iiab/iiab/iiab-network.log"
    exit 1
fi

zenity --question --width=350 --text="iiab-network complete.\n\nWould you like to REBOOT now? (Recommended)"
if [ "$?" = "0" ]; then
    x-terminal-emulator -e "sudo reboot"
fi
