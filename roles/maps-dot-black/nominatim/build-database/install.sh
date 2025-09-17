#!/bin/bash
here="$(dirname "$(readlink -f "$0")")"
cd "$here"

set -euo pipefail

export USERNAME=nominatim
export USERHOME=/srv/nominatim

sudo apt update -qq
sudo apt install -y osm2pgsql postgresql-postgis postgresql-postgis-scripts pkg-config libicu-dev virtualenv
sudo apt install -y sqlite3 libsqlite3-mod-spatialite libspatialite8

id nominatim || sudo useradd -d /srv/nominatim -s /bin/bash -m nominatim

sudo cp psql-nominatim.conf /etc/postgresql/*/main/conf.d/
sudo service postgresql restart

# Try to silently fail. Hopefully it's because the user exists already.
sudo -u postgres createuser -s        $USERNAME || echo "..."
sudo -u postgres createuser           www-data || echo "..."

# Copy it each time in case we change it
sudo cp nominatim-setup.prep /srv/nominatim/nominatim-setup.sh
sudo chown nominatim:nominatim /srv/nominatim/nominatim-setup.sh
sudo -u nominatim /srv/nominatim/nominatim-setup.sh

