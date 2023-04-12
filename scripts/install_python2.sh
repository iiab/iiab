#!/bin/bash
# https://packages.debian.org/search?keywords=libpython2.7-stdlib&searchon=names&suite=all&section=all
# https://packages.debian.org/bullseye/libpython2.7-stdlib
# https://packages.ubuntu.com/search?keywords=libpython2.7-stdlib&searchon=names&suite=all&section=all
# https://packages.ubuntu.com/jammy-updates/libpython2.7-stdlib

# payload to be installed:
# libpython2-stdlib
# libpython2.7-minimal
# libpython2.7-stdlib
# python2-minimal
# python2.7-minimal
# python2.7
# python2

export DEBIAN_FRONTEND=noninteractive
ARCH=$(dpkg --print-architecture)

apt -y install virtualenv
# https://github.com/iiab/iiab/pull/3535#issuecomment-1503626474
#apt -y install media-types libffi8 libssl3

# libpython2.7-stdlib from ubuntu-22.04 used in amd64|arm64|armhf is compiled against libssl3 and libffi8
# `apt info libpython2.7-stdlib`
cd /tmp
case $ARCH in
    "amd64")
        # works on U23.04 x86_64 VM
        cat << EOF > /etc/apt/sources.list.d/python2.list
deb [trusted=yes] http://archive.ubuntu.com/ubuntu jammy main universe
deb [trusted=yes] http://archive.ubuntu.com/ubuntu jammy-updates main universe
EOF
        ;;

    "arm64")
        # gave 404 errors on U23.04 x86_64 VM need to circle back to U23.04 arm64 and confirm
        cat << EOF > /etc/apt/sources.list.d/python2.list
deb [trusted=yes] http://ports.ubuntu.com/ jammy main universe
deb [trusted=yes] http://ports.ubuntu.com/ jammy-updates main universe
EOF
        ;;

    "armhf")
        # armhf compile flags differ between RasPiOS and Ubuntu
        if ! [ -f /etc/rpi-issue ]; then
            # these might change
            cat << EOF > /etc/apt/sources.list.d/python2.list
deb http://ports.ubuntu.com/ jammy main universe
deb http://ports.ubuntu.com/ jammy-updates main universe
EOF
        fi
        ;;
esac

apt update
apt -y install python2
rm /etc/apt/sources.list.d/python2.list || true
apt update
