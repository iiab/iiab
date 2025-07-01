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

# Cleaning previous attempts
rm -f $UPSTREAM_REPO $UPSTREAM_PIN

# There might be multiple such lines in future, e.g. if Trisquel 12 and 13 and both supported during a transitional period
[ $VERSION_CODENAME = ecne ] && UPSTREAM=noble && REPO_GPGKEY="871920D1991BC93C" && VALID_TRISQUEL_VER=1

if [ "$VALID_TRISQUEL_VER" != 1 ]; then
    echo "IIAB supports only Trisquel 12 (Ecne) for now!"
    exit 1
fi

# Prevent apparmor profiles breaking server packages.
## php-fpm profile
if [ -f "$PHP_APPARMOR_DISABLED" ]; then
    echo "- php-fpm apparmor profile disabled, moving on."
elif [ ! -f "$PHP_APPARMOR_DISABLED" ] && [ -f "$PHP_APPARMOR" ]; then
    ln -s /etc/apparmor.d/php-fpm /etc/apparmor.d/disable/
    apparmor_parser -R /etc/apparmor.d/php-fpm
fi

gpg --keyserver keyserver.ubuntu.com --recv-keys "$REPO_GPGKEY"
gpg --export "$REPO_GPGKEY" | gpg --dearmour > "$UPSTREAM_GPGKEY"

if [ "$(dpkg --print-architecture)" = amd64 ]; then
    {
    echo "# For regular x86_64/amd64"
    echo "deb http://archive.ubuntu.com/ubuntu/ ${UPSTREAM} main universe"
    echo "deb http://archive.ubuntu.com/ubuntu/ ${UPSTREAM}-updates main universe"
    echo "deb http://archive.ubuntu.com/ubuntu/ ${UPSTREAM}-security main universe"
    } | tee $UPSTREAM_REPO
else
    {
    echo "# For any other arch (especially arm64 or armhf, and potentially also ppc64el)"
    echo "deb http://ports.ubuntu.com/ubuntu-ports/ ${UPSTREAM} main universe"
    echo "deb http://ports.ubuntu.com/ubuntu-ports/ ${UPSTREAM}-updates main universe"
    echo "deb http://ports.ubuntu.com/ubuntu-ports/ ${UPSTREAM}-security main universe"
    } | tee $UPSTREAM_REPO
fi

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
tee $UPSTREAM_PIN
