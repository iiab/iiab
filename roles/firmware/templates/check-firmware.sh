#!/bin/bash
FW_MODE=$(grep wifi_hotspot_capacity_rpi_fix /etc/iiab/local_vars.yml| grep True)
WARN=0
DATE=$(date +%F-%T)
if [ -z "$FW_MODE" ]; then
    echo "FW marker not found"
else
    echo "$FW_MODE"
    if ! $(diff -q /lib/firmware/brcm/brcmfmac43455-sdio.bin.iiab /lib/firmware/brcm/brcmfmac43455-sdio.bin); then
        mv /lib/firmware/brcm/brcmfmac43455-sdio.bin /lib/firmware/brcm/brcmfmac43455-sdio.bin.$DATE
        cp /lib/firmware/brcm/brcmfmac43455-sdio.bin.iiab /lib/firmware/brcm/brcmfmac43455-sdio.bin
        echo "replacing firmware"
        WARN=1
    fi
    if ! $(diff -q /lib/firmware/brcm/brcmfmac43455-sdio.clm_blob.iiab /lib/firmware/brcm/brcmfmac43455-sdio.clm_blob); then
        mv /lib/firmware/brcm/brcmfmac43455-sdio.clm_blob /lib/firmware/brcm/brcmfmac43455-sdio.clm_blob.$DATE
        cp /lib/firmware/brcm/brcmfmac43455-sdio.clm_blob.iiab /lib/firmware/brcm/brcmfmac43455-sdio.clm_blob
        echo "replacing firmware"
        WARN=1
    fi
    if ! $(diff -q /lib/firmware/brcm/brcmfmac43430-sdio.bin.iiab /lib/firmware/brcm/brcmfmac43430-sdio.bin); then
        mv /lib/firmware/brcm/brcmfmac43430-sdio.bin /lib/firmware/brcm/brcmfmac43430-sdio.bin.$DATE
        cp /lib/firmware/brcm/brcmfmac43430-sdio.bin.iiab /lib/firmware/brcm/brcmfmac43430-sdio.bin
        cp /lib/firmware/brcm/brcmfmac43430-sdio.clm_blob.iiab /lib/firmware/brcm/brcmfmac43430-sdio.clm_blob
        echo "replacing firmware"
        WARN=1
    fi
    if ! $(diff -q /lib/firmware/brcm/brcmfmac43430-sdio.clm_blob.iiab /lib/firmware/brcm/brcmfmac43430-sdio.clm_blob); then
        mv /lib/firmware/brcm/brcmfmac43430-sdio.clm_blob /lib/firmware/brcm/brcmfmac43430-sdio.clm_blob.$DATE
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
    if [ -f /.fw_replaced ]; then
        rm /.fw_replaced
    fi
fi
exit 0
