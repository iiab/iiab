#!/bin/bash
FW_MODE=$(grep wifi_hotspot_capacity_rpi_fix /etc/iiab/local_vars.yml| grep True)
WARN=0
if [ -z "$FW_MODE" ]; then
    echo "FW marker not found"
else
    echo "$FW_MODE"
    if ! $(diff -q /lib/firmware/brcm/brcmfmac43455-sdio.bin.iiab /lib/firmware/brcm/brcmfmac43455-sdio.bin); then
        cp /lib/firmware/brcm/brcmfmac43455-sdio.bin.iiab /lib/firmware/brcm/brcmfmac43455-sdio.bin
        echo "replacing firmware"
        WARN=1
    fi
    if ! $(diff -q /lib/firmware/brcm/brcmfmac43430-sdio.bin.iiab /lib/firmware/brcm/brcmfmac43430-sdio.bin); then
        cp /lib/firmware/brcm/brcmfmac43430-sdio.bin.iiab /lib/firmware/brcm/brcmfmac43430-sdio.bin
        cp /lib/firmware/brcm/brcmfmac43430-sdio.clm_blob.iiab /lib/firmware/brcm/brcmfmac43430-sdio.clm_blob
        echo "replacing firmware"
        WARN=1
    fi
    if ! $(diff -q /lib/firmware/brcm/brcmfmac43430-sdio.clm_blob.iiab /lib/firmware/brcm/brcmfmac43430-sdio.clm_blob); then
        cp /lib/firmware/brcm/brcmfmac43430-sdio.clm_blob.iiab /lib/firmware/brcm/brcmfmac43430-sdio.clm_blob
        echo "replacing firmware"
        WARN=1
    fi
fi
if [ "$WARN" = "1" ]; then
    echo "You should reboot now"
    touch /.fw_replaced
    #echo "rebooting..."
    #reboot
else
    rm /.fw_replaced
fi
exit 0
