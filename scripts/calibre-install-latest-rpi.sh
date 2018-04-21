#!/bin/bash

# Thanks to Jerry Vonau (https://github.com/jvonau) who made
# this critical breakthrough (Calibre 3.x on Raspbian) possible!
# The latest available is 3.21 available from testing
# https://packages.debian.org/search?keywords=calibre
# (SEE http://raspbian.raspberrypi.org/raspbian/pool/main/c/calibre/ 
#  OR http://archive.raspbian.org/raspbian/pool/main/c/calibre/ ?)
# Might break future updates, you have been warned.

export DEBIAN_FRONTEND=noninteractive
# Updates calibre calibre-bin to version 3.21 or ... from testing
echo "deb http://raspbian.raspberrypi.org/raspbian/ testing main" > /etc/apt/sources.list.d/rpi-testing.list
apt update
apt -y install calibre calibre-bin
# Remove last line, safer than: rm /etc/apt/sources.list.d/debian-testing.list
sed -i '$ d' /etc/apt/sources.list.d/rpi-testing.list
# Clears the cache of testing
apt update
