# Remote support of an Internet-in-a-Box using https://remote.it

Remote.it can be a [great way](https://docs.remote.it/introduction/get-started/readme) to remotely support an Internet-in-a-Box (IIAB).

For other approaches, please see http://FAQ.IIAB.IO -> "How can I remotely manage my Internet-in-a-Box?"

## Getting Started

### Create a remote.it account + consider its desktop application

1. Browse to [https://remote.it](https://remote.it) (Web Portal) and sign up for an account.

2. Download the [remote.it desktop application](https://remote.it/download/) e.g. for Windows, macOS or Linux to your own laptop/computer &mdash; if you prefer this over the https://remote.it Web Portal and its [mobile apps](https://docs.remote.it/introduction/get-started/readme#installation-packages).

   COMPARISON: "The Desktop and [CLI](https://docs.remote.it/software/cli) can [each] support both peer to peer connections and proxy connections [whereas] the Web Portal and API can only support proxy connections" according to https://docs.remote.it/software/device-package/usage

### Install remote.it onto an IIAB + register it + authorize services/ports

1. Set `remoteit_install` and `remoteit_enabled` to `True` in your IIAB's [/etc/iiab/local_vars.yml](http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F)

2. Install and enable remote.it (its [device package](https://docs.remote.it/software/device-package)) on your IIAB, by running:

   ```
   cd /opt/iiab/iiab
   sudo ./runrole remoteit
   ```

   While rarely needed, FYI the above also installs the _optional_ `/usr/bin/remoteit` [command-line interface (CLI)](https://docs.remote.it/software/cli).

   <!--EXPLANATION: The above installs remote.it, in a way that was originally designed to be interactive, and provide you the claim code needed to make a remote connection to this IIAB.  The claim code is further explained below.-->

3. To obtain this IIAB's 8-character remote.it claim code (allowing you to make a remote connection to this IIAB) run:

   ```
   sudo grep claim /etc/remoteit/config.json
   ```

   *The claim code must be used within 24 hours, per:* https://docs.remote.it/device-package/installation#2.-update-your-package-manager-and-install

   If necessary, run this command to get a new claim code: *(adjust version & architecture in the .deb filename as appropriate!)*

   ```
   sudo apt install /opt/iiab/downloads/remoteit-4.14.1.armhf.rpi.deb
   ```

4. Submit the claim code at https://remote.it (log into the Web Portal), or within the remote.it desktop application if you installed that on your own laptop/computer.
 
   Either way, click on the '+' icon to enter the remote.it claim code (to register the IIAB device to your account) as shown in this screenshot: https://docs.remote.it/software/device-package/installation#3.-claim-and-register-the-device

5. Authorize services/ports (e.g. SSH, HTTP, etc) for your IIAB device, as shown in these screenshots: https://docs.remote.it/software/device-package/installation#4.-set-up-services-on-your-device

   SUMMARY: One or more remote.it "Services" need to be authorized (registered) to allow remote access to your IIAB device: https://support.remote.it/hc/en-us/articles/360060992631-Services

   EXAMPLES: SSH (port 22) and/or HTTP (port 80): https://support.remote.it/hc/en-us/articles/360058603991-Configuring-remoteit-Services-on-devices-with-remote-it-Desktop

## Docs

<!-- "auto-registration" of remote.it, and other more advanced configuration options, see: -->

- https://docs.remote.it
  - https://docs.remote.it/developer-tools/cli-usage
- https://support.remote.it
  - https://support.remote.it/hc/en-us/categories/360003417511-Getting-Started
- https://remote.it/resources/
  - https://remote.it/resources/blog/managing-device-access-with-remote-it/
<!-- - https://support.remote.it/hc/en-us/articles/360044424612-1-Create-an-Auto-Registration 
- https://support.remote.it/hc/en-us/articles/360044424672-1-Device-Setup-for-Auto-Bulk-Registration -->

## Known Issues

- <strike>2021-10-27: This needs to be enhanced rather urgently, so remote.it also works when IIAB is installed on Raspberry Pi OS 11 (Bullseye), Ubuntu, Mint and Debian:</strike> [#3006](https://github.com/iiab/iiab/issues/3006)
- 2021-10-29: The above OS issues should be resolved by [PR #3007](https://github.com/iiab/iiab/pull/3007), [PR #3009](https://github.com/iiab/iiab/pull/3009) and [PR #3010](https://github.com/iiab/iiab/pull/3010) &mdash; but this needs final testing!  (Initial testing occurred on [1] 32-bit Raspberry Pi OS Lite on Raspberry Pi 4 and [2] Ubuntu Server 20.04 on x86_64 VM.)
