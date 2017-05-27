#!/bin/bash -x
# this will break on machines with LVM, but other things will too

FIRSTDEV=`ls -lav /dev |grep brw| grep 'sd\|mmc' | awk 'NR==1' |awk  --field-separator=' ' '{ print $10 }'`

parted /dev/$FIRSTDEV -ms print devices
