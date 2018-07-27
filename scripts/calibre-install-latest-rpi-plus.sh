#!/bin/bash

# Calibre 3.27.1 .deb's were released for Raspbian 2018-07-22 but requires
# python-pyqt5 from debian testing, to overcome error:
#
#    The following packages have unmet dependencies:
#    calibre : Depends: python-pyqt5 (>= 5.11.2+dfsg-1) but 5.10.1+dfsg-2+rpi1 is to be installed
#
# More details @ https://github.com/iiab/iiab/issues/948 and
# https://www.mobileread.com/forums/showthread.php?p=3729117#post3729117

# Thanks to Jerry Vonau (https://github.com/jvonau) who made this critical
# breakthrough possible!
#
# SEE COMMENTS AT THE TOP OF scripts/calibre-install-packages.sh

export DEBIAN_FRONTEND=noninteractive

# Prepares to update from debian testing
apt-key adv --recv-key --keyserver keyserver.ubuntu.com 7638D0442B90D010
echo "deb http://deb.debian.org/debian testing main" >> /etc/apt/sources.list.d/debian-testing.list
apt update
apt -y install python-pyqt5
rm /etc/apt/sources.list.d/debian-testing.list

# Prepares to update from raspbian testing
echo "deb http://raspbian.raspberrypi.org/raspbian/ testing main" > /etc/apt/sources.list.d/rpi-testing.list
apt update
apt -y install calibre calibre-bin
rm /etc/apt/sources.list.d/rpi-testing.list
# Clears the cache of testing
apt update
