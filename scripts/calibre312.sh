#!/bin/bash
echo "install stock calibre-bin"
apt-get -y install calibre-bin dirmngr

echo "installing debian key"
apt-key adv --recv-key --keyserver keyserver.ubuntu.com 7638D0442B90D010

echo "enabling testing"
echo "deb http://deb.debian.org/debian testing main" > /etc/apt/sources.list.d/debian-testing.list
apt-get update

echo "updating dependencies"
apt-get -y install libqt5core5a  python-lxml
rm /etc/apt/sources.list.d/debian-testing.list

echo "enabling unstable"
echo "deb http://deb.debian.org/debian unstable main" > /etc/apt/sources.list.d/debian-unstable.list
apt-get update

echo "installing calibre 3.12"
apt-get -y install calibre
rm /etc/apt/sources.list.d/debian-unstable.list

echo "disabled testing and unstable repos"
apt-get update

echo "DONE"
