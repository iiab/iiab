#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
# drags in stock desktop dependencies without too much from testing below
apt -y install calibre-bin dirmngr

# updates calibre-bin to version 3.10 from testing
apt-key adv --recv-key --keyserver keyserver.ubuntu.com 7638D0442B90D010
echo "deb http://deb.debian.org/debian testing main" > /etc/apt/sources.list.d/debian-testing.list
apt update
apt -y install libqt5core5a  python-lxml
rm /etc/apt/sources.list.d/debian-testing.list

# updates to calibre & calibre-bin to 3.12 from unstable
echo "deb http://deb.debian.org/debian unstable main" > /etc/apt/sources.list.d/debian-unstable.list
apt update
apt -y install calibre
rm /etc/apt/sources.list.d/debian-unstable.list

# clears the cache of testing and unstable
apt update
