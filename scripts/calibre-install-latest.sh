#!/bin/bash

# Thanks to Jerry Vonau (https://github.com/jvonau) who made this critical
# breakthrough possible!
#
# Calibre 3.25 is the latest available from testing as of 2018-06-10:
#
#   https://packages.debian.org/search?keywords=calibre
#   http://deb.debian.org/debian/pool/main/c/calibre/
#   http://raspbian.raspberrypi.org/raspbian/pool/main/c/calibre/
#   http://archive.raspbian.org/raspbian/pool/main/c/calibre/
#
# Might break future updates; you have been warned.

export DEBIAN_FRONTEND=noninteractive
# Drags in stock desktop dependencies without too much from testing below
apt -y install dirmngr
# Prepares to update to latest from testing
apt-key adv --recv-key --keyserver keyserver.ubuntu.com 7638D0442B90D010
echo "deb http://deb.debian.org/debian testing main" >> /etc/apt/sources.list.d/debian-testing.list
apt update
apt -y install libqt5core5a python-lxml calibre calibre-bin
# Removes last line, safer than: rm /etc/apt/sources.list.d/debian-testing.list
sed -i '$ d' /etc/apt/sources.list.d/debian-testing.list
# Clears the cache of testing
apt update
