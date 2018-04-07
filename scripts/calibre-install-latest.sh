#!/bin/bash

# Thanks to Jerry Vonau (https://github.com/jvonau) who made
# this critical breakthrough for Calibre 3.x possible!
# The latest available is 3.20 available from testing
# https://packages.debian.org/search?keywords=calibre
# (SEE http://deb.debian.org/debian/pool/main/c/calibre/ ?)
# might break future updates, you have been warned

export DEBIAN_FRONTEND=noninteractive
# Drags in stock desktop dependencies without too much from testing below
apt -y install calibre-bin dirmngr
# Updates calibre calibre-bin to version 3.20 or ... from testing
apt-key adv --recv-key --keyserver keyserver.ubuntu.com 7638D0442B90D010
echo "deb http://deb.debian.org/debian testing main" >> /etc/apt/sources.list.d/debian-testing.list
apt update
apt -y install libqt5core5a python-lxml calibre
# Remove last line, safer than: rm /etc/apt/sources.list.d/debian-testing.list
sed -i '$ d' /etc/apt/sources.list.d/debian-testing.list
apt update
