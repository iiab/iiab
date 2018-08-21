#!/bin/bash

# Calibre 3.29 requires this approach, to overcome error:
#
#    calibre-bin : Depends: qtbase-abi-5-10-0 but it is not installable
#   E: Unable to correct problems, you have held broken packages.
#
# Above error proved insurmountable when trying most all scripts in /opt/iiab/iiab/scripts -- even those that DID solve this error:
#
#    calibre : Depends: python-pyqt5 (>= 5.11.2+dfsg-1+b1)

# Thanks to Jerry Vonau (https://github.com/jvonau) who made this critical
# breakthrough possible!
#
# SEE NOTES AT TOP OF scripts/calibre-install-packages.sh

export DEBIAN_FRONTEND=noninteractive
# Drags in stock desktop dependencies without too much from testing below
apt -y install dirmngr
# Prepares to update to latest from debian testing
apt-key adv --recv-key --keyserver keyserver.ubuntu.com 7638D0442B90D010
echo "deb http://deb.debian.org/debian testing main" >> /etc/apt/sources.list.d/debian-testing.list
apt update
apt -y install libqt5core5a python-lxml calibre calibre-bin
## Removes last line, safer than: rm /etc/apt/sources.list.d/debian-testing.list
#sed -i '$ d' /etc/apt/sources.list.d/debian-testing.list
rm /etc/apt/sources.list.d/debian-testing.list
# Clears the cache of testing
apt update
