#!/bin/bash

# Thanks to Jerry Vonau (https://github.com/jvonau) who made this critical
# breakthrough possible!
#
# Calibre 3.23 is the latest available from testing as of 2018-05-10:
#
#   http://raspbian.raspberrypi.org/raspbian/pool/main/c/calibre/
#   http://archive.raspbian.org/raspbian/pool/main/c/calibre/
#   https://packages.debian.org/search?keywords=calibre
#   http://deb.debian.org/debian/pool/main/c/calibre/
#
# Might break future updates; you have been warned.

export DEBIAN_FRONTEND=noninteractive
# Prepare to update to latest from testing
echo "deb http://raspbian.raspberrypi.org/raspbian/ testing main" > /etc/apt/sources.list.d/rpi-testing.list
apt update
apt -y install calibre calibre-bin
# Remove last line, safer than: rm /etc/apt/sources.list.d/rpi-testing.list
sed -i '$ d' /etc/apt/sources.list.d/rpi-testing.list
# Clears the cache of testing
apt update
