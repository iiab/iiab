#!/bin/bash
# Remove symlink in /library/content to automounted usb drive
#
DEVICE=$(echo $@ | sed -s 's|-|/|')
MNT_POINT=$(findmnt -n /$DEVICE | awk '{print $1}')
CONTENT_LINK_USB=$(basename $MNT_POINT | awk '{print toupper($0)}')
CONTENT_LINK="/library/www/html/local_content/$CONTENT_LINK_USB"
logger -p user.notice -t "usb_lib (iiab-clean-usb.sh)" -- "Attempting to remove link $CONTENT_LINK, as auto-created earlier by usbmount."

if [ -L $CONTENT_LINK ]; then
  /bin/rm $CONTENT_LINK
  logger -p user.notice -t "usb_lib (iiab-clean-usb.sh)" -- "$CONTENT_LINK removed."
fi

