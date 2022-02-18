#!/bin/bash -x

# Resize rootfs and its partition on the RPi SD card (or external USB
# disk if possible, e.g. with Raspberry Pi OS) to maximum size.

# To be used by /etc/systemd/system/iiab-rpi-root-resize.service on boot.
# Only resizes if /.resize-rootfs exists.
# Assumes root is last partition.

if [ -f /.resize-rootfs ]; then
    echo "$0: maximizing rootfs partion"

    if [ -x /usr/bin/raspi-config ]; then
        # 2022-02-17: Works in many more situations, e.g. with USB disks (not
        # just microSD cards).  IF ONLY THIS ALSO WORKED ON Ubuntu/Mint/etc !

        # Uses do_expand_rootfs() from:
        # https://github.com/RPi-Distro/raspi-config/blob/master/raspi-config
        raspi-config --expand-rootfs
    else
        # ASSUMES SD CARD STYLE PARTITION NAME LIKE <device>p<partition number>
        # e.g. /dev/mmcblk0p2 mounts at /           (typical RasPiOS microSD)
        # BUT  /dev/sda2      mounts at /media/usb1 (typical RasPiOS USB boot
        #                                            disk WON'T WORK BELOW!)

        # Calculate root partition
        root_part=`lsblk -aP -o NAME,MOUNTPOINT | grep 'MOUNTPOINT="/"' | awk -F\" '{ print $2 }'`    # e.g. mmcblk0p2
        root_dev=${root_part:0:-2}    # e.g. mmcblk0
        # bash substring expansion: "negative offset [below, but not above]
        # must be separated from the colon by at least one space to avoid
        # being confused with the ‘:-’ expansion"
        # https://www.gnu.org/software/bash/manual/html_node/Shell-Parameter-Expansion.html
        root_part_no=${root_part: -1}    # e.g. 2

        # Resize partition
        growpart /dev/$root_dev $root_part_no
        resize2fs /dev/$root_part
    fi

    rm /.resize-rootfs
fi
