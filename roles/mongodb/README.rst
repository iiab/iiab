==============
mongodb README
==============

New installs of Debain 13 on amd64 use version 9 from mongodb's trixie, code change need for Debian 14

New installs on Ubuntu 2404 and derivatives plus Debian 13 arm64 use version 9 based on mongodb's noble

New installs on Ubuntu 2604+ and derivatives plus Debian 14 arm64 use version 9 based on mongodb's resolute

New installs on RasPiOS 13 or any Ubuntu version on arm64 rpi hardware use version 5 based on mongodb's focal
with an overlay rolling the installed debs files back to version 5.0.5 It is possible to install version 9 on
rpi hardware by adding 'rpi_arm_version: "9.0"' to local vars to alter the behavior of the installer, this is
currently untested.

Older mongodb installs using version 5.0 or 6.0 are blocked from being upgraded due to needing staged upgrades
from the current versions. The code will actively detect if version 5.0 or 6.0 deb packages are installed and 
will always override '--reinstall' to protect current data. Staged upgrades might come in the future.

On all version mongodb is not enabled in systemd, the service is started via sugarizer's unit file via Requires=
