#!/bin/bash

# Thanks to Jerry Vonau (https://github.com/jvonau) who made
# this critical breakthrough possible!
# might break future updates, you have been warned
# The latest available is 3.20 available from testing
# https://packages.debian.org/search?keywords=calibre
# might break future updates, you have been warned

export DEBIAN_FRONTEND=noninteractive
# Updates to calibre & calibre-bin to "very latest" 3.x from unstable
echo "deb http://deb.debian.org/debian unstable main" >> /etc/apt/sources.list.d/unstable.list
apt update
apt -y install calibre calibre-bin
# Remove last line, safer than: rm /etc/apt/sources.list.d/debian-unstable.list
sed -i '$ d' /etc/apt/sources.list.d/unstable.list
# Clears the cache of testing and unstable
apt update
