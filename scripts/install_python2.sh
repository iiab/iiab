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

# 2023-05-19: #3573 -> PR #3582: Ubuntu 23.10's virtualenv 20.23 no longer
# supports Python 2.  Root cause is virtualenv 20.22.0 (2023-04-19) which
# removed Python 2 support: https://virtualenv.pypa.io/en/latest/changelog.html
# Unfortunately older versions from Ubuntu 22.04 (#3583) & 23.04 like...
# http://launchpadlibrarian.net/651276954/virtualenv_20.19.0+ds-1_all.deb
# ...can drag in newer 20.23+ version of python3-virtualenv, leaving
# us with /usr/bin/virtualenv 20.23 once again, i.e. preventing Python 2.
# Whereas pip (which installs /usr/local/bin/virtualvenv) at least works:
#
#iif grep -qi ubuntu /etc/os-release; then    # Ubuntu 23.10+ (and Mint 22+ ?) needs this.  Ubuntu 23.04 tolerates it.
#    apt -y install python3-pip
#    pip install virtualenv==20.21.1 --break-system-packages
#else
#    apt -y install virtualenv    # Debian 12 & RasPiOS 12 are A-Ok with built-in virtualenv 20.17.1 (<= 20.21.1)
#fi
#
#apt -y install virtualenv
# https://github.com/iiab/iiab/pull/3535#issuecomment-1503626474
#apt -y install media-types libffi8 libssl3

# libpython2.7-stdlib from ubuntu-22.04 used in amd64|arm64|armhf is compiled against libssl3 and libffi8
# `apt info libpython2.7-stdlib`
#cd /tmp

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
        if [ -f /etc/rpi-issue ] && ! grep -q 11 /etc/issue; then    # RasPiOS 12+ / Bookworm+
            cat << EOF > /etc/apt/sources.list.d/python2.list
deb [trusted=yes] http://ports.ubuntu.com/ jammy main universe
deb [trusted=yes] http://ports.ubuntu.com/ jammy-updates main universe
EOF
#         elif ! [ -f /etc/rpi-issue ]; then    # Ubuntu/Debian on armhf not supported
#             cat << EOF > /etc/apt/sources.list.d/python2.list
# deb http://ports.ubuntu.com/ jammy main universe
# deb http://ports.ubuntu.com/ jammy-updates main universe
# EOF
        fi
        ;;

    "i386")
        # Building on scripts/ansible fix PR #3615
        if grep -q '^ID=debian$' /etc/os-release; then
            cat << EOF > /etc/apt/sources.list.d/python2.list
deb http://deb.debian.org/debian bullseye main contrib non-free
deb http://deb.debian.org/debian bullseye-updates main contrib non-free
EOF
        fi
        ;;
esac

apt update
if grep -qi ubuntu /etc/os-release; then    # Ubuntu 23.10+ (and Mint 22+ ?) needs this.  Ubuntu 23.04 tolerates it.
    # 2023-05-20: 4 lines below borrow from Ubuntu 22.04: (Is this really less
    # fragile than the pip approach ~40 lines above, in preparing for 24.04 ?)
    apt -y install python3-platformdirs=2.5.1-1
    apt-mark hold python3-platformdirs
    apt -y install python3-virtualenv=20.13.0+ds-2
    apt-mark hold python3-virtualenv    # 2023-09-26: 'apt-mark hold virtualenv' was definitely insufficient on Ubuntu 23.10
    # 2023-05-21 PR #3587: Above 4 lines should really install a more recent
    # version of virtualenv, probably from 'lunar' (Ubuntu 23.04) ?
else
    apt -y install virtualenv    # Debian 12 & RasPiOS 12 are A-Ok with built-in virtualenv 20.17.1 (<= 20.21.1)
fi
apt -y install python2
rm /etc/apt/sources.list.d/python2.list || true
apt update
