#!/bin/bash

# Thanks to Jerry Vonau (https://github.com/jvonau) who made this critical
# breakthrough possible!
#
# CLARIF: this entire file (calibre-install-packages.sh) is hopefully no
# longer necessary after June 21, 2018.
#
# CONTEXT: calibre-install-latest-rpi.sh worked up to Calibre 3.23 in May 2018
# -- and once again began working when Calibre 3.26.0 .debs became available
# from http://raspbian.raspberrypi.org/raspbian/pool/main/c/calibre/ on June
# 20, 2018 -- but had failed (#831) to "apt install" Calibre 3.24.x and 3.25
# during early and mid-June 2018, with error message:
#
#   The following packages have unmet dependencies:
#    calibre : Depends: python-pyqt5 (>= 5.10.1+dfsg-2) but 5.10.1+dfsg-1+rpi1 is to be installed
#   E: Unable to correct problems, you have held broken packages.

# In the interim (June 18-21, 2018) the following 3-step recipe for RPi was
# briefly used: (to permit microSD's that were at least interoperable between
# RPi 3 / 3 B+ & Zero W, even if Calibre did not run in Zero W)
#
# 1. "apt install calibre calibre-bin" (both 2.75.1, part of Raspbian OS)
#
# 2. calibre-install-packages.sh installs those packages that
#    calibre-install-latest-rpi.sh had used to install for Calibre 3.23:
#
#    https://github.com/iiab/iiab/pull/839
#
# 3. calibre-install-latest.sh installs Debian's own calibre & calibre-bin etc:
#
#    https://github.com/iiab/iiab/pull/833    # WORKED ON RPI 3 AND RPI 3 B+ BUT...
#    https://github.com/iiab/iiab/issues/835  # FAILED ON RPI ZERO W, possibly due to libc6 (IF ABOVE STEP 2 NOT RUN!)

# FYI Calibre 3.26.1 and 3.27.1 are the latest available from testing as of 2018-07-10:
#
#   http://raspbian.raspberrypi.org/raspbian/pool/main/c/calibre/
#   http://archive.raspbian.org/raspbian/pool/main/c/calibre/
#   https://packages.debian.org/search?keywords=calibre
#   http://deb.debian.org/debian/pool/main/c/calibre/ ~= http://cdn-fastly.deb.debian.org/debian/pool/main/c/calibre/
#
# Might break future updates; you have been warned.

export DEBIAN_FRONTEND=noninteractive
# Prepares to update to latest from testing
echo "deb http://raspbian.raspberrypi.org/raspbian/ testing main" > /etc/apt/sources.list.d/rpi-testing.list
apt update
# Packages below cribbed from Calibre 3.23 installation on 2018-05-22, as recorded in /var/log/apt/history.log*
apt -y install libegl1 libegl-mesa0 libqt5sensors5 libbrotli1 libwoff1 libpodofo0.9.5 libjs-coffeescript python-regex libhyphen0 libqt5webchannel5 python-msgpack python-html5-parser libqt5positioning5 libpcre2-16-0 libglvnd0 libdrm-common python-sip libqt5svg5 libnih-dbus1 qt5-gtk-platformtheme libc6-dbg libqt5help5 libc6-dev libqt5dbus5 libqt5sql5-sqlite libc6 libqt5widgets5 locales libegl1-mesa python-pyqt5.qtsvg python-lxml fontconfig-config libqt5xml5 libgbm1 libqt5printsupport5 libqt5qml5 libc-l10n libqt5gui5 libc-bin libnih1 libqt5webkit5 python-pyqt5.qtwebkit libdrm2 libqt5core5a libfontconfig1 libqt5opengl5 libc-dev-bin python-pyqt5 libqt5network5 libqt5designer5 libqt5quick5 libqt5sql5
# BUT DO NOT DO "apt -y install calibre calibre-bin" UNTIL calibre-install-latest.sh ?
#sed -i '$ d' /etc/apt/sources.list.d/rpi-testing.list    # Removes last line
rm /etc/apt/sources.list.d/rpi-testing.list
# Clears the cache of rpi/testing
apt update
