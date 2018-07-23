#!/bin/bash

# Thanks to Jerry Vonau (https://github.com/jvonau) who made this critical
# breakthrough possible!
#
# SEE COMMENTS AT THE TOP OF scripts/calibre-install-packages.sh

export DEBIAN_FRONTEND=noninteractive
# Prepares to update to latest from raspbian testing
echo "deb http://raspbian.raspberrypi.org/raspbian/ testing main" > /etc/apt/sources.list.d/rpi-testing.list
apt update
apt -y install calibre calibre-bin
## Removes last line, safer than: rm /etc/apt/sources.list.d/rpi-testing.list
#sed -i '$ d' /etc/apt/sources.list.d/rpi-testing.list
rm /etc/apt/sources.list.d/rpi-testing.list
# Clears the cache of testing
apt update
