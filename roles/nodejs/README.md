Please see IIAB's recommended Node.js version number [around line 439 of /opt/iiab/iiab/vars/default_vars.yml](https://github.com/iiab/iiab/blob/master/vars/default_vars.yml#L434-L439)

If Nodesource.com doesn't yet support your OS
---------------------------------------------

Nodesource.com often supports Debian long before each Debian release, whereas for other OS's, Nodesource.com support usually arrives a few days or weeks after the OS release.

For late-breaking details on Nodesource.com support for your particular Linux OS, keep an eye on:

- https://github.com/nodesource/distributions#deb
- https://deb.nodesource.com/node_20.x/dists/
  - https://deb.nodesource.com/node_20.x/pool/main/n/nodejs/
  - https://nodejs.org/dist/latest-v20.x/
- https://deb.nodesource.com/node_19.x/dists/
  - https://deb.nodesource.com/node_19.x/pool/main/n/nodejs/
  - https://nodejs.org/dist/latest-v19.x/
- _ETC!_

If Nodesource.com does not yet support your Linux OS and IIAB's asked to install Node.js &mdash; IIAB will then [fall back](https://github.com/iiab/iiab/blob/91a5cd33f34d5d2a55e75bf0cdc85bcd9d7b4821/roles/nodejs/tasks/install.yml#L103-L107) to: (running the equivalent of)

```
sudo apt install nodejs npm
sudo echo 'nodejs_installed: True' >> /etc/iiab/iiab_state.yml
```

(The above installs your OS's own versions of Node.js and npm.)

Separately, if you later want to try **wiping** nodejs and npm (AT YOUR OWN RISK!) to attempt the Nodesource approach instead, run:

```
cd /opt/iiab/iiab
sudo ./runrole --reinstall nodejs
```

Raspberry Pi Zero W Warning
---------------------------

UPDATE: The Zero 2 W released 2021-10-28 is 64-bit (ARMv7) so may not have such serious problems...

On the original Raspberry Pi Zero W (ARMv6) however: Node.js applications like Internet Archive, JupyterHub, Node-RED, PBX (Asterisk/FreePBX) and Sugarizer won't work — if you installed Node.js while on Raspberry Pi 3, 3 B+ (ARMv7) or Raspberry Pi 4 (ARMv8).

If necessary, run `sudo apt purge nodejs npm` then `sudo rm /etc/apt/sources.list.d/nodesource.list` then  `sudo apt update` and then attempt to [install Node.js](https://github.com/iiab/iiab/blob/master/roles/nodejs/tasks/install.yml) _on the Raspberry Pi Zero W itself_ (`cd /opt/iiab/iiab` then `sudo ./runrole --reinstall nodejs`).

Earlier, some preferred installing the tar file version mentioned at [#2082](https://github.com/iiab/iiab/issues/2082#issuecomment-569344617) &mdash; if that is your preference, consider a more recent version like: https://nodejs.org/dist/latest-v20.x/

Either way, you'll (likely) then also need to run: `sudo apt install npm`

Whatever versions of Node.js and npm you install, make sure `/etc/iiab/iiab_state.yml` contains the line `nodejs_installed: True` (add it if necessary!)  Finally, proceed to install Internet Archive, JupyterHub, Node-RED ([Raspberry Pi notes](https://nodered.org/docs/hardware/raspberrypi#swapping-sd-cards)), PBX (Asterisk/FreePBX) and/or Sugarizer: [#1799](https://github.com/iiab/iiab/issues/1799)
