#!/bin/bash
# https://packages.debian.org/bullseye/libpython2.7-stdlib
ARCH=$(dpkg --print-architecture)

apt -y install virtualenv
apt -y install mime-support #transitional package
#apt -y install libffi8

cd /tmp
case $ARCH in
    "arm64")
        wget http://archive.raspberrypi.org/debian/pool/main/o/openssl/libssl1.1_1.1.1n-0+deb11u4+rpt1_arm64.deb
        apt install ./libssl1.1_1.1.1n-0+deb11u4+rpt1_arm64.deb

        wget http://ftp.debian.org/debian/pool/main/libf/libffi/libffi7_3.3-6_arm64.deb
        apt install ./libffi7_3.3-6_arm64.deb

        wget http://ftp.debian.org/debian/pool/main/p/python2.7/libpython2.7-minimal_2.7.18-8_arm64.deb
        apt install ./libpython2.7-minimal_2.7.18-8_arm64.deb

        wget http://ftp.debian.org/debian/pool/main/p/python2.7/libpython2.7-stdlib_2.7.18-8_arm64.deb
        apt install ./libpython2.7-stdlib_2.7.18-8_arm64.deb

        wget http://ftp.debian.org/debian/pool/main/p/python2.7/python2.7-minimal_2.7.18-8_arm64.deb
        apt install ./python2.7-minimal_2.7.18-8_arm64.deb

        wget http://ftp.debian.org/debian/pool/main/p/python2.7/python2.7_2.7.18-8_arm64.deb
        apt install ./python2.7_2.7.18-8_arm64.deb
        ;;

    "amd64")
        wget http://security.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2.17_amd64.deb
        apt install ./libssl1.1_1.1.1f-1ubuntu2.17_amd64.deb

        wget http://mirrors.edge.kernel.org/ubuntu/pool/universe/libf/libffi7/libffi7_3.3-5ubuntu1_amd64.deb
        apt install ./libffi7_3.3-5ubuntu1_amd64.deb

        wget http://mirrors.edge.kernel.org/ubuntu/pool/universe/p/python2.7/libpython2.7-minimal_2.7.18-13ubuntu2_amd64.deb
        apt install ./libpython2.7-minimal_2.7.18-13ubuntu2_amd64.deb

        wget http://mirrors.edge.kernel.org/ubuntu/pool/universe/p/python2.7/libpython2.7-stdlib_2.7.18-13ubuntu2_amd64.deb
        apt install ./libpython2.7-stdlib_2.7.18-13ubuntu2_amd64.deb

        wget http://mirrors.edge.kernel.org/ubuntu/pool/universe/p/python2.7/python2.7-minimal_2.7.18-13ubuntu2_amd64.deb
        apt install ./python2.7-minimal_2.7.18-13ubuntu2_amd64.deb

        wget http://mirrors.kernel.org/ubuntu/pool/universe/p/python2.7/python2.7_2.7.18-13ubuntu2_amd64.deb
        apt install ./python2.7_2.7.18-13ubuntu2_amd64.deb
        ;;

    "armhf")
        wget http://archive.raspberrypi.org/debian/pool/main/o/openssl/libssl1.1_1.1.1n-0+deb11u4+rpt1_armhf.deb
        apt install ./libssl1.1_1.1.1n-0+deb11u4+rpt1_armhf.deb

        wget http://raspbian.raspberrypi.org/raspbian/pool/main/libf/libffi/libffi7_3.3-6_armhf.deb
        apt install ./libffi7_3.3-6_armhf.deb

        wget http://raspbian.raspberrypi.org/raspbian/pool/main/p/python2.7/libpython2.7-minimal_2.7.18-13.2_armhf.deb
        apt install ./libpython2.7-minimal_2.7.18-13.2_armhf.deb

        wget http://raspbian.raspberrypi.org/raspbian/pool/main/p/python2.7/libpython2.7-stdlib_2.7.18-13.2_armhf.deb
        apt install ./libpython2.7-stdlib_2.7.18-13.2_armhf.deb

        wget http://raspbian.raspberrypi.org/raspbian/pool/main/p/python2.7/python2.7-minimal_2.7.18-13.2_armhf.deb
        apt install ./python2.7-minimal_2.7.18-13.2_armhf.deb

        wget http://raspbian.raspberrypi.org/raspbian/pool/main/p/python2.7/python2.7-minimal_2.7.18-13.2_armhf.deb
        apt install ./python2.7_2.7.18-13.2_armhf.deb
        ;;
esac
rm *.deb
