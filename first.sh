#!/bin/bash
# recognize OS, and other first things
OS=`grep ^ID= /etc/*elease | cut -d= -f2`
export OS
VERSION_ID=`grep VERSION_ID /etc/*elease | cut -d= -f2`
VER=${VERSION_ID%%\"}
VER=${VER##\"}
VER=${VER%%.*}
OS_CONTEXT=$OS-$VER
export OS_CONTEXT

