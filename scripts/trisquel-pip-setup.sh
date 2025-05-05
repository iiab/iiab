#!/bin/bash

if [ "$EUID" -ne 0 ]; then
   echo "This script must be run as root"
   exit 1
fi

. /etc/os-release
UPSTREAM_REPO="/etc/apt/sources.list.d/upstream_repo.list"
UPSTREAM_PIN="/etc/apt/preferences.d/python3-pip"
UPSTREAM_GPGKEY="/etc/apt/trusted.gpg.d/upstream_repo.gpg"
PHP_APPARMOR=/etc/apparmor.d/php-fpm
PHP_APPARMOR_DISABLED=/etc/apparmor.d/disable/php-fpm

# Cleaning previos attempts
rm -f $UPSTREAM_REPO $UPSTREAM_PIN

[ $VERSION_CODENAME = ecne ] && UPSTREAM=noble && REPO_GPGKEY="871920D1991BC93C" && VALID=1

if [ "$VALID" != 1 ]; then
    echo "Not valid codename"
    exit 1
fi

# Prevent apparmor profiles breaking server packages.
apt-get -y install curl
if [ -f "$PHP_APPARMOR_DISABLED" ];  then
   echo "- php-fpm apparmor profile disabled, moving on."
elif [ ! -f "$PHP_APPARMOR_DISABLED" ] && [ -f "$PHP_APPARMOR" ]; then
    ln -s /etc/apparmor.d/php-fpm /etc/apparmor.d/disable/
    apparmor_parser -R /etc/apparmor.d/php-fpm
fi

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
