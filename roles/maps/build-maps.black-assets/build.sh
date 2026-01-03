#!/bin/bash

# Make sure we're in the right directory
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd $SCRIPT_DIR

set -euo pipefail

curl -fsSL https://deb.nodesource.com/setup_24.x | sudo bash - &&\
sudo apt install -y nodejs

git clone https://github.com/iiab/maps.black
cd maps.black
git checkout 12205728ceb0672682381088c6c1e7ad05fdc4f5
cd client

npm ci
npm run prebuild
npm run build-http
