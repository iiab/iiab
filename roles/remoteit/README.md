# Installing Remoteit on a Raspberry Pi
1. Set remoteit_install and remoteit_enabled to True in /etc/local_vars.yml.
2 Run the role that installs remote.it.`
```
    ./runroles remoteit
```
3. The last step installs the remoteit code. But the last part of the install is designed to be interactive, and returns a registration code which i required to make the connection from your remoteit global registration. So run the last step to retrieve and record the registration number.
```
    cd /opt/iiab/downloads
    apt reinstall ./remoteit-4.13.5.armhf.rpi.deb
```
3. After you have installed the remote.it client desktop on your laptop, click on the + icon, and enter the registration number displayed in step #3.
