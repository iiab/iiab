# Remote support of an Internet-in-a-Box using https://remote.it

Remote.it can be a great way to remotely support an Internet-in-a-Box (IIAB).  

For other approaches, please see http://FAQ.IIAB.IO -> "How can I remotely manage my Internet-in-a-Box?"

## Getting Started

### Create a remote.it account

1. Go to the [https://remote.it](https://remote.it) website and sign up for an account.
2. OPTIONAL: Download [remote.it's desktop application](https://remote.it/download/) e.g. for Windows, macOS or Linux.

### Install remote.it onto an IIAB

1. Set `remoteit_install` and `remoteit_enabled` to `True` in your IIAB's [/etc/iiab/local_vars.yml](http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F)

2. Install and enable it (remote.it) on your IIAB, by running:

   ```
   cd /opt/iiab/iiab
   sudo ./runrole remoteit
   ```
   <!--EXPLANATION: The above installs remote.it, in a way that was originally designed to be interactive, and provide you the claim code needed to make a remote connection to this IIAB.  The claim code is further explained below.-->

3. To obtain this IIAB's 8-character remote.it claim code, allowing you to make a remote connection to this IIAB, run:

   ```
   sudo grep claim /etc/remoteit/config.json
   ```

   *The claim code must be used within 24 hours, per:* https://docs.remote.it/device-package/installation#2.-update-your-package-manager-and-install

   If not used before then, here is an *example (version & architecture can change in the .deb filename below!)* to re-run this installation command, to get a new claim code:

   ```
   sudo apt reinstall /opt/iiab/downloads/remoteit-4.13.6.armhf.rpi.deb
   ```

4. After you've installed the https://remote.it client software onto a separate computer or device (e.g. your own laptop) click on the '+' icon, then enter the remote.it claim code (for the IIAB that you need to connect to).

   As shown in the screenshot here: https://docs.remote.it/device-package/installation#3.-claim-and-register-the-device

### Usage Summary

1. Log into the https://remote.it Web Portal, or open its desktop application.
2. Add Devices (e.g. your IIAB).
3. Understand that each Device will need to contain one or more remote.it Services.
   - Add a remote.it Service (e.g. HTTP and/or others) to your Device:<br>https://support.remote.it/hc/en-us/articles/360050732092-Add-a-remote-it-Service-to-your-Device

Summary of remote.it Services: https://support.remote.it/hc/en-us/articles/360060992631-Services

For more info, please see remote.it's [Getting Started pages](https://support.remote.it/hc/en-us/categories/360003417511-Getting-Started).

## Advanced

For "auto-registration" of remote.it, and other more advanced configuration options, please review:

- https://docs.remote.it
- https://support.remote.it
- https://support.remote.it/hc/en-us/articles/360044424612-1-Create-an-Auto-Registration
- https://support.remote.it/hc/en-us/articles/360044424672-1-Device-Setup-for-Auto-Bulk-Registration

## Known Issues

- 2021-10-27: This needs to be enhanced rather urgently, so remote.it also works when IIAB is installed on Raspberry Pi OS 11 (Bullseye), Ubuntu, Mint and Debian: [#3006](https://github.com/iiab/iiab/issues/3006)
- 2021-10-29: The above OS issues should be resolved by [PR #3007](https://github.com/iiab/iiab/pull/3007), [PR #3009](https://github.com/iiab/iiab/pull/3009) and [PR #3010](https://github.com/iiab/iiab/pull/3010) &mdash; but this needs final testing!  (Initial testing occurred on [1] 32-bit Raspberry Pi OS Lite on Raspberry Pi 4 and [2] Ubuntu Server 20.04 on x86_64 VM.)
