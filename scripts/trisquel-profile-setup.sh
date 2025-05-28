#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root"
    exit 1
fi

. /etc/os-release
UPSTREAM_REPO="/etc/apt/sources.list.d/upstream_repo.list"
UPSTREAM_PIN="/etc/apt/preferences.d/python3-pip"
UPSTREAM_GPGKEY="/etc/apt/trusted.gpg.d/upstream_repo.gpg"
APPARMOR_DIR=/etc/apparmor.d
APPARMOR_DISABLED_DIR=/etc/apparmor.d/disable

# Cleaning previous attempts
rm -f $UPSTREAM_REPO $UPSTREAM_PIN

# There might be multiple such lines in future, e.g. if Trisquel 12 and 13 and both supported during a transitional period
[ $VERSION_CODENAME = ecne ] && UPSTREAM=noble && REPO_GPGKEY="871920D1991BC93C" && VALID_TRISQUEL_VER=1

if [ "$VALID_TRISQUEL_VER" != 1 ]; then
    echo "IIAB supports only Trisquel 12 (Ecne) for now!"
    exit 1
fi

# Prevent apparmor profiles breaking server packages.
for i in php-fpm transmission
do
    if [ -f "$APPARMOR_DISABLED_DIR/$i" ]; then
        echo "- $i apparmor profile disabled, moving on."
    elif [ ! -f "$APPARMOR_DISABLED_DIR/$i" ] && [ -f "$APPARMOR_DIR/$i" ]; then
        ln -s "$APPARMOR_DIR/$i" "$APPARMOR_DISABLED_DIR/"
        apparmor_parser -R "$APPARMOR_DIR/$i"
    fi
done

gpg --keyserver keyserver.ubuntu.com --recv-keys "$REPO_GPGKEY"
gpg --export "$REPO_GPGKEY" | gpg --dearmour > "$UPSTREAM_GPGKEY"

echo "
deb http://archive.ubuntu.com/ubuntu/ ${UPSTREAM} main universe
deb http://archive.ubuntu.com/ubuntu/ ${UPSTREAM}-updates main universe
deb http://archive.ubuntu.com/ubuntu/ ${UPSTREAM}-security main universe" | \
sudo tee $UPSTREAM_REPO

echo "
Package: python3-pip
Pin: release n=$UPSTREAM
Pin-Priority: 500

Package: python3-pip-whl
Pin: release n=$UPSTREAM
Pin-Priority: 500

Package: *
Pin: release n=$UPSTREAM
Pin-Priority: -1" | \
sudo tee $UPSTREAM_PIN
