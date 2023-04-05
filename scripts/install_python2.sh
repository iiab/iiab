#!/bin/bash
ARCH=$(dpkg --print-architecture)
cd /tmp
case $ARCH in
    "arm64")
        wget http://ftp.debian.org/debian/pool/main/p/python2.7/libpython2.7-minimal_2.7.18-8_arm64.deb
        apt install ./libpython2.7-minimal_2.7.18-8_arm64.deb
        wget http://ftp.debian.org/debian/pool/main/p/python2.7/python2.7-minimal_2.7.18-8_arm64.deb
        apt install ./python2.7-minimal_2.7.18-8_arm64.deb
        ;;
    "amd64")
        wget http://ftp.debian.org/debian/pool/main/p/python2.7/libpython2.7-minimal_2.7.18-8_amd64.deb
        apt install ./libpython2.7-minimal_2.7.18-8_amd64.deb
        wget http://ftp.debian.org/debian/pool/main/p/python2.7/python2.7-minimal_2.7.18-8_amd64.deb
        apt install ./python2.7-minimal_2.7.18-8_amd64.deb
        ;;
    "armhf")
        wget http://raspbian.raspberrypi.org/raspbian/pool/main/p/python2.7/libpython2.7-minimal_2.7.18-13.2_armhf.deb
        apt install ./libpython2.7-minimal_2.7.18-13.2_armhf.deb
        wget http://raspbian.raspberrypi.org/raspbian/pool/main/p/python2.7/python2.7-minimal_2.7.18-13.2_armhf.deb
        apt install ./libpython2.7-minimal_2.7.18-13.2_armhf.deb
        ;;
esac
rm *.deb
apt -y install virtualenv
