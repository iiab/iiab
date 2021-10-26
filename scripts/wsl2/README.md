# Get Started with Ubuntu on Windows System for Linux 2

1. Open a ```cmd``` prompt. 
1. The ```wsl``` windows 11 command manages Linux virtual machines
    1. ```wsl --list --online``` Find out what virtual machines are available for download.
    2. ```wsl -l -v``` Find out what virtual machines are on this machine.
    3. ```wsl --install -d Ubuntu```   Install one of the virtual machines available.
2. Download the most recent Ubuntu distribution.
3. This with ask for a username and password, and land you in a terminal.
4. Become root: ```sudo su```
5. Download the IIAB code that runs on WSL:
```
   cd /opt
   mkdir iiab
   cd iiab
   git clone https://github.com/georgejhunt/iiab -b wsl
   cd /opt/iiab/iiab/scripts/wsl
   # Run the script which causes wsl Ubuntu to use systemd for startup (required by ansible)
   ./ubuntu-wsl2-systemd-script.sh
```
6. Copy the vars/local_vars_wsl.yml to /etc/iiab/local_vars.yml
7. At this point, you can probably run the oneline IIAB installer to completion (will not modify network) but will install the Admin Console

### ubuntu-wsl2-systemd-script

The followin README fragment is from: https://github.com/damiongans/ubuntu-wsl2-systemd-script

Script to enable systemd support on current Ubuntu WSL2 images from the Windows store. 
Script is unsupported and will no longer be maintained, but will be up here because it is used by quite some people.
I am not responsible for broken installations, fights with your roommates and police ringing your door ;-).

Instructions from [the snapcraft forum](https://forum.snapcraft.io/t/running-snaps-on-wsl2-insiders-only-for-now/13033) turned into a script. Thanks to [Daniel](https://forum.snapcraft.io/u/daniel) on the Snapcraft forum! 

## Usage
You need ```git``` to be installed for the commands below to work. Use
```sh
sudo apt install git
```
to do so.
### Run the script and commands
```sh
git clone https://github.com/DamionGans/ubuntu-wsl2-systemd-script.git
cd ubuntu-wsl2-systemd-script/
bash ubuntu-wsl2-systemd-script.sh
# Enter your password and wait until the script has finished
```
### Then restart the Ubuntu shell and try running systemctl
```sh
systemctl

```
If you don't get an error and see a list of units, the script worked.

Have fun using systemd on your Ubuntu WSL2 image. You may use and change and distribute this script in whatever way you'd like. 
