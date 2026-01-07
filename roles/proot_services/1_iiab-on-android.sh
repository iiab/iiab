#!/bin/bash
# This is a convenient script to test the current Android IIAB implementation
# it requires that you install termux, once on it install proot-distro.

# PRoot-Distro allows to install multiple OSes, we use Debian then login.

# See more details at:
# - https://github.com/iiab/iiab/blob/master/vars/local_vars_android.yml

set -e

#-----------------------------
# Safety checks
#-----------------------------
if [ $UID != 0 ]; then
    echo "This script should be run as root, which is the default in proot-distro"
    echo "Careful, maybe this script is not been executed on the right terminal?"
    exit 1
fi

#-----------------------------
# Config
#-----------------------------
LOCAL_VARS="https://raw.githubusercontent.com/deldesir/iiab/refs/heads/master/vars/local_vars_android.yml"
PR="4122"
OWNER="iiab"
REPO="iiab"
INSTALL_URL="https://iiab.io/install.txt"
API="https://api.github.com/repos/${OWNER}/${REPO}"

# Update package db
apt-get update

# Install basic dependencies
apt-get install -y curl \
                   python3 \
                   sudo \
                   nano \
                   git

#-----------------------------
# Setup Android-specific local vars
#-----------------------------
mkdir -p /etc/iiab
# Prefer local file if we are running from the repo
if [ ! -f /etc/iiab/local_vars.yml ]; then
    if [ -f "vars/local_vars_android.yml" ]; then
        cp vars/local_vars_android.yml /etc/iiab/local_vars.yml
    elif [ -f "/opt/iiab/iiab/vars/local_vars_android.yml" ]; then
        cp /opt/iiab/iiab/vars/local_vars_android.yml /etc/iiab/local_vars.yml
    else
        curl -fsSL $LOCAL_VARS > /etc/iiab/local_vars.yml
    fi
else
    echo "   Preserving existing /etc/iiab/local_vars.yml"
fi

if [ "$IIAB_PAUSE_BEFORE_INSTALL" = "true" ]; then
    echo ""
    echo "=================================================================="
    echo " PAUSED: IIAB_PAUSE_BEFORE_INSTALL=true"
    echo "=================================================================="
    echo " You can now edit the configuration file:"
    echo "   nano /etc/iiab/local_vars.yml"
    echo ""
    echo " Open a new terminal session (or background this one) to edit."
    echo " When you are ready to proceed with installation, press Enter."
    echo "=================================================================="
    read -p "Press Enter to continue..."
fi

#-----------------------------
# Run complete Android build
#-----------------------------
#-----------------------------
# Run complete Android build
#-----------------------------
## Clone the specific repo requested by user (deldesir/iiab)
## This prevents the default installer from cloning iiab/iiab upstream
mkdir -p /opt/iiab
if [ -d /opt/iiab/iiab ]; then
    echo "Repo /opt/iiab/iiab already exists, updating..."
    cd /opt/iiab/iiab
    git pull
else
    echo "Cloning deldesir/iiab..."
    git clone https://github.com/deldesir/iiab.git /opt/iiab/iiab
    cd /opt/iiab/iiab
    # Ensure we are on master (or preferred branch)
    git checkout master 2>/dev/null || git checkout main
fi

# Run the standard installer (it will detect valid /opt/iiab/iiab and use it)
curl -fsSL "$INSTALL_URL" | bash
exit 0
