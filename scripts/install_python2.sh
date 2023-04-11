#!/bin/bash
# https://packages.debian.org/bullseye/libpython2.7-stdlib
ARCH=$(dpkg --print-architecture)

apt -y install virtualenv
apt -y install mime-support #transitional package

# libpython2.7-stdlib from ubuntu-22.04 used in amd64 is compiled against libssl3 and libffi8
# `apt info libpython2.7-stdlib`
cd /tmp
case $ARCH in
    #"amd64")
        #wget http://mirrors.edge.kernel.org/ubuntu/pool/main/libf/libffi/libffi8_3.4.2-4_amd64.deb
        #apt install ./libffi8_3.4.2-4_amd64.deb

        #wget http://mirrors.edge.kernel.org/ubuntu/pool/universe/p/python2.7/libpython2.7-minimal_2.7.18-13ubuntu2_amd64.deb
        #apt install ./libpython2.7-minimal_2.7.18-13ubuntu2_amd64.deb

        #wget http://mirrors.edge.kernel.org/ubuntu/pool/universe/p/python2.7/libpython2.7-stdlib_2.7.18-13ubuntu2_amd64.deb
        #apt install ./libpython2.7-stdlib_2.7.18-13ubuntu2_amd64.deb

        #wget http://mirrors.edge.kernel.org/ubuntu/pool/universe/p/python2.7/python2.7-minimal_2.7.18-13ubuntu2_amd64.deb
        #apt install ./python2.7-minimal_2.7.18-13ubuntu2_amd64.deb

        #wget http://mirrors.kernel.org/ubuntu/pool/universe/p/python2.7/python2.7_2.7.18-13ubuntu2_amd64.deb
        #apt install ./python2.7_2.7.18-13ubuntu2_amd64.deb
        #;;

    #"arm64")
        #wget http://ftp.debian.org/debian/pool/main/libf/libffi/libffi7_3.3-6_arm64.deb
        #apt install ./libffi7_3.3-6_arm64.deb

        #wget http://ftp.debian.org/debian/pool/main/p/python2.7/libpython2.7-minimal_2.7.18-8_arm64.deb
        #apt install ./libpython2.7-minimal_2.7.18-8_arm64.deb

        #wget http://ftp.debian.org/debian/pool/main/p/python2.7/libpython2.7-stdlib_2.7.18-8_arm64.deb
        #apt install ./libpython2.7-stdlib_2.7.18-8_arm64.deb

        #wget http://ftp.debian.org/debian/pool/main/p/python2.7/python2.7-minimal_2.7.18-8_arm64.deb
        #apt install ./python2.7-minimal_2.7.18-8_arm64.deb

        #wget http://ftp.debian.org/debian/pool/main/p/python2.7/python2.7_2.7.18-8_arm64.deb
        #apt install ./python2.7_2.7.18-8_arm64.deb
        #;;

# trusted is used for Debian and RasPiOS as the keys would be missing for Ubuntu
    "arm64"|"amd64")
        apt -y install libffi8
        cat << EOF >> /etc/apt/sources.list.d/python2.list
deb [trusted=yes] http://ports.ubuntu.com/ jammy main universe
deb [trusted=yes] http://ports.ubuntu.com/ jammy-updates main universe
EOF
        ;;

    "armhf")
        #wget http://raspbian.raspberrypi.org/raspbian/pool/main/libf/libffi/libffi7_3.3-6_armhf.deb
        #apt install ./libffi7_3.3-6_armhf.deb

        #wget http://raspbian.raspberrypi.org/raspbian/pool/main/p/python2.7/libpython2.7-minimal_2.7.18-13.2_armhf.deb
        #apt install ./libpython2.7-minimal_2.7.18-13.2_armhf.deb

        #wget http://raspbian.raspberrypi.org/raspbian/pool/main/p/python2.7/libpython2.7-stdlib_2.7.18-13.2_armhf.deb
        #apt install ./libpython2.7-stdlib_2.7.18-13.2_armhf.deb

        #wget http://raspbian.raspberrypi.org/raspbian/pool/main/p/python2.7/python2.7-minimal_2.7.18-13.2_armhf.deb
        #apt install ./python2.7-minimal_2.7.18-13.2_armhf.deb

        #wget http://raspbian.raspberrypi.org/raspbian/pool/main/p/python2.7/python2.7_2.7.18-13.2_armhf.deb
        #apt install ./python2.7_2.7.18-13.2_armhf.deb
        #rm *.deb

        if [ -f /etc/rpi-issue ]; then
            cat << EOF >> /etc/apt/sources.list.d/python2.list
deb http://raspbian.raspberrypi.org/raspbian/ bullseye main
deb http://archive.raspberrypi.org/debian/ bullseye main
EOF
        else
            cat << EOF >> /etc/apt/sources.list.d/python2.list
deb http://ports.ubuntu.com/ jammy main universe
deb http://ports.ubuntu.com/ jammy-updates main universe
EOF
        fi
        ;;
esac

apt update
apt -y install python2
rm /etc/apt/sources.list.d/python2.list
apt update
