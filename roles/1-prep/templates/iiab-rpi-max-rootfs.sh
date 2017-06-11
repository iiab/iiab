#!/bin/bash -x
# Resize rootfs and its partition on the rpi SD card to maximum size
# To be used by systemd service on boot
# Only resizes if /.resize-rootfs exists
# Assumes root is last partition
# Only works on F22 + where resizepart command exists
# Assumes sd card style partition name like <device>p<partition number>

if [  -f /.resize-rootfs ];then
  echo "$0: maximizing rootfs partion"
  # Calculate root partition
  root_part=`lsblk -aP -o NAME,MOUNTPOINT|grep  'MOUNTPOINT="/"' |awk -F\" '{ print $2 }'`
  root_dev=${root_part:0:-2}
  root_part_no=${root_part: (-1)}

  # Resize partition
  parted -s /dev/$root_dev resizepart $root_part_no 100%
  resize2fs /dev/$root_part
  rm /.resize-rootfs
fi
