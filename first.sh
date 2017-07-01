#!/bin/bash
# recognize OS, and other first things
OS=`grep ^ID= /etc/*elease | cut -d= -f2`
# centos encloses the ID in quites -- clip them
OS=${OS##\"}
OS=${OS%%\"}
export OS
VERSION_ID=`grep VERSION_ID /etc/*elease | cut -d= -f2`
VER=${VERSION_ID%%\"}
VER=${VER##\"}
# ubuntu currently gives us 16.04, use major number
VER=${VER%%.*}
OS_VER=$OS-$VER
export OS_VER

