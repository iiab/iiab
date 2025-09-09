#!/bin/bash
here="$(dirname "$(readlink -f "$0")")"
cd "$here"

set -euo pipefail

export USERNAME=nominatim
export USERHOME=/srv/nominatim

sudo apt update -qq
# Install: postgres stuff, sqlite3 stuff, downloading stuff
sudo apt install -y \
    osm2pgsql postgresql-postgis postgresql-postgis-scripts pkg-config libicu-dev virtualenv \
    sqlite3 libsqlite3-mod-spatialite libspatialite8 \
    aria2

id $USERNAME || sudo useradd -d $USERHOME -s /bin/bash -m $USERNAME

if [ -z ${DEV+x} ];
  then (echo "Optimizing for the beefy server"; sudo cp psql-nominatim.conf /etc/postgresql/*/main/conf.d/);
  else (echo "Optimizing for development"; sudo rm -f /etc/postgresql/*/main/conf.d/psql-nominatim.conf);
fi

sudo service postgresql restart

# Try to silently fail. Hopefully it's because the user exists already.
sudo -u postgres createuser -s        $USERNAME || echo "..."
sudo -u postgres createuser           www-data || echo "..."

# Copy these each time in case we change them
sudo cp nominatim-setup.prep $USERHOME/nominatim-setup.sh
sudo chown $USERNAME:$USERNAME $USERHOME/nominatim-setup.sh

sudo cp iiab.lua $USERHOME/iiab.lua
sudo chown $USERNAME:$USERNAME $USERHOME/iiab.lua

sudo -u $USERNAME $USERHOME/nominatim-setup.sh
