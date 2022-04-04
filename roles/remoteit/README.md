# Remote support of an Internet-in-a-Box using https://remote.it

Remote.it can be a [great way](https://docs.remote.it/introduction/get-started/readme) to remotely support an Internet-in-a-Box (IIAB).

As of [April 2022](https://remote.it/pricing/), 5 IIAB devices can be managed for free, and an unlimited number can be managed for $6/month.

For other approaches, please see http://FAQ.IIAB.IO -> "How can I remotely manage my Internet-in-a-Box?"

## Getting Started

### Create a remote.it account + install its desktop application

1. Browse to [https://remote.it](https://remote.it) (Web Portal) and sign up for an account.

2. Download and install the remote.it [desktop application](https://remote.it/download/) (e.g. for Windows, macOS or Linux) on your own laptop/computer.  Their https://remote.it Web Portal and [mobile apps](https://docs.remote.it/introduction/get-started/readme#installation-packages) are also sometimes possible, but less functional.

   COMPARISON: "The Desktop and [CLI](https://docs.remote.it/software/cli) can [each] support both peer to peer connections and proxy connections [whereas] the Web Portal and API can only support proxy connections" according to https://docs.remote.it/software/device-package/usage

<!-- ### Install remote.it onto an IIAB + register it + authorize services/ports -->
### Generate a remote.it claim code for your IIAB + register it + authorize services/ports

Prerequisite: Find an IIAB with `remoteit_installed: True` in `/etc/iiab/iiab_state.yml`.

1. Run `sudo iiab-remoteit`

   Hit `[Enter]` twice if you want to quickly generate a new claim code for your IIAB.

   The claim code is stored in `/etc/remoteit/config.json` and must be used [within 24 hours](https://docs.remote.it/device-package/installation#2.-update-your-package-manager-and-install).

<!--
1. Connect your IIAB device to the Internet.

2. If your IIAB software is already installed, run `sudo iiab-remoteit` then skip to Step 5. below.

3. If your IIAB software isn't yet installed, set `remoteit_install` and `remoteit_enabled` to `True` in its [/etc/iiab/local_vars.yml](https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F)

   Install [IIAB software](https://download.iiab.io/) e.g. by running `sudo iiab` then follow any on-screen instructions &mdash; until "INTERNET-IN-A-BOX (IIAB) SOFTWARE INSTALL IS COMPLETE" eventually appears on screen.
-->

   <!-- , and when that's complete go directly to Step 3. below.

   Then install and enable remote.it (its [Device Package](https://docs.remote.it/software/device-package)) on your IIAB, by running:

   ```
   cd /opt/iiab/iiab
   sudo ./runrole remoteit
   ```

   Or if necessary reinstall the latest, by running:

   ```
   cd /opt/iiab/iiab
   sudo ./runrole --reinstall remoteit
   ``` -->

<!--
(This installs and enables the remote.it [Device Package](https://docs.remote.it/software/device-package) for your CPU and OS.  This also installs the _optional_ `/usr/bin/remoteit` [command-line interface (CLI)](https://docs.remote.it/software/cli), which offers [a few more features](https://support.remote.it/hc/en-us/articles/4412786750861-Install-the-remoteit-agent-on-your-device) than the Device Package.)

4. To obtain your IIAB's 8-character remote.it claim code (allowing you to make a remote connection to this IIAB device) run:

   ```
   sudo grep claim /etc/remoteit/config.json
   ```

   *The claim code must be used within 24 hours, per:* https://docs.remote.it/device-package/installation#2.-update-your-package-manager-and-install

   _If your claim code has expired, please run_ `sudo iiab-remoteit` _just as in Step 2._
-->

   <!-- If necessary, run this command to get a new claim code: *(adjust version & architecture in the .deb filename as appropriate!)*

   ```
   sudo apt install /opt/iiab/downloads/remoteit-4.14.1.armhf.rpi.deb
   ``` -->

2. Submit the claim code within the remote.it [desktop application](https://remote.it/download/) on your own laptop/computer.  Or if you prefer, do that by logging into their Web Portal at: https://remote.it
 
   Either way, click on the '+' icon to enter the remote.it claim code (to register the IIAB device to your account) as shown in this [screenshot](https://docs.remote.it/software/device-package/installation#3.-claim-and-register-the-device).

3. Authorize services/ports (e.g. SSH, HTTP, etc) for your IIAB device, as shown in these [screenshots](https://docs.remote.it/software/device-package/installation#4.-set-up-services-on-your-device).

   SUMMARY: One or more remote.it "Services" need to be authorized (registered) to allow remote access to your IIAB device:<br>https://support.remote.it/hc/en-us/articles/360060992631-Services

   EXAMPLES: SSH (port 22) and/or HTTP (port 80):<br>https://support.remote.it/hc/en-us/articles/360058603991-Configuring-remoteit-Services-on-devices-with-remote-it-Desktop

### How to I disable remote.it on my IIAB?

1. Run `sudo nano /etc/iiab/local_vars.yml` to set `remoteit_enabled: False`

2. Then run:

   ```
   cd /opt/iiab/iiab
   sudo ./runrole remoteit
   ```

3. If want to completely remove the remote.it software and its settings, also run:

   ```
   sudo apt purge "remoteit*"
   sudo rm /usr/bin/remoteit
   ```

## Docs

<!-- "auto-registration" of remote.it, and other more advanced configuration options, see: -->

- https://docs.remote.it
  - https://docs.remote.it/developer-tools/cli-usage
- https://support.remote.it
  - https://support.remote.it/hc/en-us/categories/360003417511-Getting-Started
  - https://support.remote.it/hc/en-us/articles/360061228252-Oops-I-cloned-an-SD-card-
  - https://support.remote.it/hc/en-us/articles/360041590951-Why-does-the-address-time-out-
  - https://support.remote.it/hc/en-us/articles/4422773654669-Streamlined-installation-for-Linux-and-Raspberry-Pi-platforms
  - https://support.remote.it/hc/en-us/articles/360051668711-Updating-the-remoteit-or-connectd-packages-using-a-remote-it-SSH-connection
  <!-- - https://support.remote.it/hc/en-us/articles/360044424612-1-Create-an-Auto-Registration 
  - https://support.remote.it/hc/en-us/articles/360044424672-1-Device-Setup-for-Auto-Bulk-Registration -->
- https://remote.it/resources/
  - https://remote.it/resources/blog/managing-device-access-with-remote-it/
- https://remote.it/legal/
  - https://remote.it/legal/fair-use-policy/

## Known Issues

- <strike>2021-10-27: This needs to be enhanced rather urgently, so remote.it also works when IIAB is installed on Raspberry Pi OS 11 (Bullseye), Ubuntu, Mint and Debian:</strike> [#3006](https://github.com/iiab/iiab/issues/3006)
- 2021-10-29: The above OS issues should be resolved by [PR #3007](https://github.com/iiab/iiab/pull/3007), [PR #3009](https://github.com/iiab/iiab/pull/3009) and [PR #3010](https://github.com/iiab/iiab/pull/3010) &mdash; but this needs final testing!  (Initial testing occurred on [1] 32-bit Raspberry Pi OS Lite on Raspberry Pi 4 and [2] Ubuntu Server 20.04 on x86_64 VM.)
