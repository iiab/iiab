#!/bin/bash
here="$(dirname "$(readlink -f "$0")")"
cd "$here"

set -euo pipefail

export USERNAME=nominatim
export USERHOME=/srv/nominatim

sudo apt-get update -qq
sudo apt-get install -y osm2pgsql postgresql-postgis postgresql-postgis-scripts \
                        pkg-config libicu-dev virtualenv

id nominatim || sudo useradd -d /srv/nominatim -s /bin/bash -m nominatim

# Copy it each time in case we change it
sudo cp nominatim-setup.prep /srv/nominatim/nominatim-setup.sh
sudo chown nominatim:nominatim /srv/nominatim/nominatim-setup.sh
sudo -u nominatim /srv/nominatim/nominatim-setup.sh

sudo cp psql-nominatim.conf /etc/postgresql/*/main/conf.d/
sudo service postgresql restart

# drop first so I can re-run this script
sudo -u postgres dropuser --if-exists $USERNAME
sudo -u postgres createuser -s        $USERNAME
sudo -u postgres dropuser --if-exists www-data
sudo -u postgres createuser           www-data
