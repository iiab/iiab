Please see IIAB's recommended Node.js version number [around line 439 of /opt/iiab/iiab/vars/default_vars.yml](https://github.com/iiab/iiab/blob/master/vars/default_vars.yml#L434-L439)

If nodesource.com doesn't yet support your OS
---------------------------------------------

If nodesource.com [does not yet support your Linux OS (they often support Debian pre-releases, but generally not other OS pre-releases)](https://github.com/nodesource/distributions#deb) then you can manually install an older version of Node.js and npm as follows:

- `sudo apt install nodejs npm`
- `sudo echo 'nodejs_installed: True' >> /etc/iiab/iiab_state.yml`

Best to do this prior to installing IIAB!

See also late-breaking details about your individual OS:

- https://github.com/nodesource/distributions#deb
- https://github.com/iiab/iiab/wiki/IIAB-Platforms

Raspberry Pi Zero W Warning
---------------------------

Node.js applications like Asterisk/FreePBX, Node-RED and Sugarizer won't work on Raspberry Pi Zero W (ARMv6) if you installed Node.js while on RPi 3, 3 B+ (ARMv7) or RPi 4 (ARMv8).

If necessary, run `apt remove nodejs` or `apt purge nodejs` then `rm /etc/apt/sources.list.d/nodesource.list; apt update` then ([attempt!](https://nodered.org/docs/hardware/raspberrypi#swapping-sd-cards)) to [install Node.js](https://github.com/iiab/iiab/blob/master/roles/nodejs/tasks/main.yml) _on the Raspberry Pi Zero W itself_ (a better approach than "cd /opt/iiab/iiab; ./runrole --reinstall nodejs" is to try `apt install nodejs` or try installing the tar file mentioned at [#2082](https://github.com/iiab/iiab/issues/2082#issuecomment-569344617)).

You'll (likely) also need `apt install npm`.

Whatever versions of Node.js and npm you install, make sure `/etc/iiab/iiab_state.yml` contains the line `nodejs_installed: True` (add it if nec!)  Finally, proceed to install Asterisk/FreePBX, Node-RED and/or Sugarizer: [#1799](https://github.com/iiab/iiab/issues/1799)
