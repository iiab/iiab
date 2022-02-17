#!/bin/bash -x

# Resize rootfs and its partition on the rpi SD card (or external USB
# disk if possible, e.g. with Raspberry Pi OS) to maximum size.

# To be used by /etc/systemd/system/iiab-rpi-root-resize.service on boot.
# Only resizes if /.resize-rootfs exists.
# Assumes root is last partition.

if [ -f /.resize-rootfs ]; then
    echo "$0: maximizing rootfs partion"

    if [ -x /usr/bin/raspi-config ]; then
        # 2022-02-17: Works in many more situations, e.g. with USB disks (not
        # just microSD cards).  IF ONLY THIS ALSO WORKED ON Ubuntu/Mint/etc !
        raspi-config --expand-rootfs
    else
        # Assumes sd card style partition name like <device>p<partition number>
        # Only works on F22 + where resizepart command exists

        # Calculate root partition
        root_part=`lsblk -aP -o NAME,MOUNTPOINT | grep  'MOUNTPOINT="/"' | awk -F\" '{ print $2 }'`
        root_dev=${root_part:0:-2}
        root_part_no=${root_part: (-1)}

        # Resize partition
        growpart /dev/$root_dev $root_part_no
        resize2fs /dev/$root_part
    fi

    rm /.resize-rootfs
fi
