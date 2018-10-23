#!/bin/bash

# Thanks to Jerry Vonau (https://github.com/jvonau) who made this critical
# breakthrough possible!
#
# Might break future updates; you have been warned.
# SEE NOTES AT TOP OF scripts/calibre-install-packages.sh

export DEBIAN_FRONTEND=noninteractive
# Prepares to update to latest from raspbian testing
echo "deb http://raspbian.raspberrypi.org/raspbian/ testing main" > /etc/apt/sources.list.d/rpi-testing.list
apt update
# WARNING: you MUST remove old .deb's from /opt/iiab/downloads if upgrading Calibre in this way, SEE: http://FAQ.IIAB.IO "Can I upgrade or reinstall server apps?"
apt -y install sqlite3    # Appears no longer nec as of 2018-10-23.  Was required in Sept 2018 as workaround for https://github.com/iiab/iiab/issues/1139 that blocked install of Admin Console
#sed -i '$ d' /etc/apt/sources.list.d/rpi-testing.list    # Removes last line
rm /etc/apt/sources.list.d/rpi-testing.list
# Clears the cache of rpi/testing
apt update
