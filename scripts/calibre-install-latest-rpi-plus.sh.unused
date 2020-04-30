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
# Might break future updates; you have been warned.
# SEE NOTES AT TOP OF scripts/calibre-install-packages.sh

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
apt -y install sqlite3    # Appears no longer nec as of 2018-10-23.  Was required in Sept 2018 as workaround for https://github.com/iiab/iiab/issues/1139 that blocked install of Admin Console
rm /etc/apt/sources.list.d/rpi-testing.list
# Clears the cache of rpi/testing
apt update
