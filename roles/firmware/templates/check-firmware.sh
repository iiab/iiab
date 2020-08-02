#!/bin/bash
FW_MODE=$(grep wifi_hotspot_capacity_rpi_fix /etc/iiab/local_vars.yml| grep True)
WARN=0
if [ -z "$FW_MODE" ]; then
    echo "FW marker not found"
else
    echo "$FW_MODE"
    if ! $(diff -q /lib/firmware/brcm/brcmfmac43455-sdio.bin.iiab /lib/firmware/brcm/brcmfmac43455-sdio.bin); then
        cp /lib/firmware/brcm/brcmfmac43455-sdio.bin.iiab /lib/firmware/brcm/brcmfmac43455-sdio.bin
        WARN=1
    fi
    if ! $(diff -q /lib/firmware/brcm/brcmfmac43430-sdio.bin.iiab /lib/firmware/brcm/brcmfmac43430-sdio.bin); then
        cp /lib/firmware/brcm/brcmfmac43430-sdio.bin.iiab /lib/firmware/brcm/brcmfmac43430-sdio.bin
        WARN=1
    fi
fi
if [ "$WARN" = "1" ]
    touch /.fw_replaced
else
    rm /.fw_replaced
fi
exit 0
