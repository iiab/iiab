#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
# Drags in stock desktop dependencies without too much from testing below
apt -y install calibre-bin dirmngr

# Updates calibre-bin to version 3.10 from testing
apt-key adv --recv-key --keyserver keyserver.ubuntu.com 7638D0442B90D010
echo "deb http://deb.debian.org/debian testing main" >> /etc/apt/sources.list.d/debian-testing.list
apt update
apt -y install libqt5core5a python-lxml calibre
# Remove last line, safer than: rm /etc/apt/sources.list.d/debian-testing.list
sed -i '$ d' /etc/apt/sources.list.d/debian-testing.list

# Updates to calibre & calibre-bin to 3.12 from unstable
echo "deb http://deb.debian.org/debian unstable main" >> /etc/apt/sources.list.d/debian-unstable.list
apt update
apt -y install calibre
# Remove last line, safer than: rm /etc/apt/sources.list.d/debian-unstable.list
sed -i '$ d' /etc/apt/sources.list.d/debian-unstable.list

# Clears the cache of testing and unstable
apt update
