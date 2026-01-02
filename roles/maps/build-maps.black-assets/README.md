This directory is for building a custom files/maps.black.js using [our fork of maps.black](https://github.com/iiab/maps.black).

# Building

Warning: You may want to run this in a VM. It will install nodejs from nodesource, not your OS's repository. It will also install npm packages.

To build:

* copy `build.sh` to a Debian-based build environment
* run `./build.sh` (takes just a couple minutes to build everything)
* copy the built `./maps.black/client/client/maps.black.js` out of your build environment
* save it to `roles/maps/files/maps.black.js` in the iiab repository and commit it

# Upstream updates

The build process appears to be deterministic. If you build maps.black.js based on the version that we originally forked from, it is identical (as of Jan 2026) to https://v1.maps.black/maps.black.js.

If maps.black makes a new release, we can rebase. We should also then update maps.black's other assets specified at default/main.yml. We could confirm that the new rebase point corresponds to the expected version by building it and comparing it to https://v2.maps.black/maps.black.js (or wherever it ends up).
