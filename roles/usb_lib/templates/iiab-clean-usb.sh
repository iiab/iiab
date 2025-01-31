#!/bin/bash
# Remove symlink in /library/www/html/local_content to automounted USB drive

DEVICE="/$(echo $1 | sed 's|-|/|')"
MNT_POINT=$(findmnt -no target $DEVICE)
CONTENT_LINK_USB=$(basename $MNT_POINT | awk '{print toupper($0)}')
CONTENT_LINK="/library/www/html/local_content/$CONTENT_LINK_USB"

logger -t "usb_lib (iiab-clean-usb.sh)" "Attempting to remove symlink $CONTENT_LINK, as auto-created earlier by usbmount."

if [ -L $CONTENT_LINK ]; then
    /usr/bin/rm $CONTENT_LINK
    logger -t "usb_lib (iiab-clean-usb.sh)" "Symlink $CONTENT_LINK removed, as auto-created earlier by usbmount."
fi
