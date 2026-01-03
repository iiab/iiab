#!/bin/bash

# Make sure we're in the right directory
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd $SCRIPT_DIR

set -euo pipefail

curl -fsSL https://deb.nodesource.com/setup_24.x | sudo bash - &&\
sudo apt install -y nodejs

git clone https://github.com/iiab/maps.black
cd maps.black
git checkout c1baf6d07f181ff62f9c272060056640dbec9c7f
cd client

npm ci
npm run prebuild
npm run build-http
