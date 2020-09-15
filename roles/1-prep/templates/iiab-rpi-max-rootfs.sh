#!/bin/bash -x
# Resize rootfs and its partition on the rpi SD card to maximum size
# To be used by systemd service on boot
# Only resizes if /.resize-rootfs exists
# Assumes root is last partition
# Only works on F22 + where resizepart command exists
# Assumes sd card style partition name like <device>p<partition number>

echo "Checking for .resize-rootfs"
if [  -f /.resize-rootfs ];then
  echo "$0: maximizing rootfs partion"
  # Calculate root partition
  root_part=`lsblk -aP -o NAME,MOUNTPOINT|grep  'MOUNTPOINT="/"' |awk -F\" '{ print $2 }'`
  root_dev=${root_part:0:-2}
  root_part_no=${root_part: (-1)}

  # Resize partition
  growpart /dev/$root_dev $root_part_no
  resize2fs /dev/$root_part
  rm /.resize-rootfs
fi
exit 0
