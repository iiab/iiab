Please see IIAB's recommended Node.js version number [around line 439 of /opt/iiab/iiab/vars/default_vars.yml](https://github.com/iiab/iiab/blob/master/vars/default_vars.yml#L434-L439)

If nodesource.com doesn't yet support your OS
---------------------------------------------

If nodesource.com [does not yet support your Linux OS (they often support Debian pre-releases, but generally not other OS pre-releases)](https://github.com/nodesource/distributions#deb) and IIAB's asked to install Node.js, it will do the equivalent of:

- `sudo apt install nodejs npm`
- `sudo echo 'nodejs_installed: True' >> /etc/iiab/iiab_state.yml`

AT YOUR OWN RISK, you can later run `cd /opt/iiab/iiab` then `sudo ./runrole --reinstall nodejs` if you really want to **wipe** your OS's own versions of Node.js and npm, and attempt the Nodesource approach instead.

See also late-breaking details on Nodesource support for your individual OS:

- https://github.com/nodesource/distributions#deb
- https://deb.nodesource.com/node_18.x/dists/
  - https://deb.nodesource.com/node_18.x/pool/main/n/nodejs/
- https://deb.nodesource.com/node_19.x/dists/
  - https://deb.nodesource.com/node_19.x/pool/main/n/nodejs/
- _ETC!_

Raspberry Pi Zero W Warning
---------------------------

Node.js applications like Asterisk/FreePBX, Node-RED and Sugarizer won't work on Raspberry Pi Zero W (ARMv6) if you installed Node.js while on RPi 3, 3 B+ (ARMv7) or RPi 4 (ARMv8).

If necessary, run `sudo apt purge nodejs npm` then `sudo rm /etc/apt/sources.list.d/nodesource.list` then  `sudo apt update` and then attempt to [install Node.js](https://github.com/iiab/iiab/blob/master/roles/nodejs/tasks/install.yml) _on the Raspberry Pi Zero W itself_ (`cd /opt/iiab/iiab` then `sudo ./runrole --reinstall nodejs`).

Earlier, some preferred installing the tar file version mentioned at [#2082](https://github.com/iiab/iiab/issues/2082#issuecomment-569344617) &mdash; and if so, consider a more recent version like https://nodejs.org/dist/latest-v18.x/

You'll (likely) also then need to run: `sudo apt install npm`

Whatever versions of Node.js and npm you install, make sure `/etc/iiab/iiab_state.yml` contains the line `nodejs_installed: True` (add it if nec!)  Finally, proceed to install Asterisk/FreePBX, Node-RED ([Raspberry Pi notes](https://nodered.org/docs/hardware/raspberrypi#swapping-sd-cards)) and/or Sugarizer: [#1799](https://github.com/iiab/iiab/issues/1799)
