# Internet-in-a-Box on Android

Internet-in-a-Box (IIAB) on Android means that millions of people worldwide can build their own family libraries, inside their own phones.

As of January 2026, these IIAB Apps are supported:

- Caliber-Web
- Kiwix
- Kolibri
- Maps
- Matomo

The default port for the web server is **8085**, for example:

    http://localhost:8085/maps

## Installation

1) Install **Termux**:

   - https://github.com/Termux/Termux-app/releases/

2) Enable **Developer Options** on Android.

3) Remove / increase app child processes limit to install and run IIAB.

   - On Android 14 and later, it is possible to disable this restriction using Android's Settings, in a *Developer options* setting called:
     - `Disable child process restriction` (English) or
     - `Desactivar restricciones de procesos secundarios` (Spanish)

   - Android 12 and 13 added a ["Phantom Process Killer" (PPK)](https://github.com/agnostic-apollo/Android-Docs/blob/master/en/docs/apps/processes/phantom-cached-and-empty-processes.md) feature to limit child processes, but there is no UI interface to disable this behavior (on Android 12 and 13).  Instead, you can disable it using ADB commands issued from a remote device, or within the device itself by using **[Shizuku](https://github.com/RikkaApps/Shizuku/releases/)**.

     Shizuko is a 3 step process **Pair**, **Run** and **Export**.  Please check the video (WIP) tutorial for a more interactive explantaion, once exporte the `0_termux_setup.sh` script will deal witht he PPK workaround setup.

4) Prepare Termux-app, use the following command from the Termux terminal.

   ```
   curl -s https://raw.githubusercontent.com/iiab/iiab/refs/heads/master/roles/proot_services/0_termux-setup.sh | bash
   ```

   Once complete please enter the debian environment to continue the installation:

   ```
   proot-distro login debian
   ```

5) Install local_vars_android.yml to /etc/iiab/local_vars.yml and run IIAB's installer in order to install the current setup.

   Once on the proot-distro environment you can install IIAB running the following script:

   ```
   curl -s https://raw.githubusercontent.com/iiab/iiab/refs/heads/master/roles/proot_services/1_iiab-on-android.sh | bash
   ```

   If the installer completes correclty you have finished the installation process.
   If you run into an error or problem, please open an [issue](https://github.com/iiab/iiab/issues) so we can help you and others, as quickly as possible.

## Remote Access

Even while using the phone keyboard and screen is very practical when on the move, being able to access the proot-distro
environment from a PC or Laptop will be very useful when trying to debug an issue.  You can use the Wi-Fi connection, or even 
establish the native Android Hotspot from your phone if there is no wireless LAN available.

Get your phone IP by using the `ifconfig` on Termux or looking at the About device > Status window.

### ssh

In order to access de IIAB install, the default way to do it is to access **Termux**, the CLI (command-line interface) on you phone from you computer via ssh, 
you can accomplish that by...

1) Setup ssh credentials (on Termux, not proot-distro).

   The fastest way to ssh into your device is to set a password to your Termux user. On Termux (not proot-distro) type:

   ```
   passwd
   ```

   and set the password.

   Security can be improved following the standard ssh keys setup on `~/.ssh/authorized_keys` file.

2) Starting the ssh service from Termux (not proot-distro).

   You need to start ssh in order to use it,

   ```
   sshd
   ```

   The sshd service can be automized to start at Termux launch (see [Termux-services](https://wiki.Termux.com/wiki/Termux-services)), 
   we would recommend that you only set it up, once you've improved the login security using ssh keys.

3) Access your Android phone:

   Once on your laptop / PC, connected to the same network that your Android phone, and having the phone IP (e.g.: 192.168.10.100)

   Use the following command:

   ```
   ssh -p 8022 192.168.10.100
   ```

   You are not required to use an specific user, and you might have noticed that you require to use port 8022.  

   Since Android is running without root permissions, then ssh can't use lower ports, due to this restriction we use port 8085 for the webserver / nginx as a workaround for the lack of port 80.

### Login IIAB environment

Once on ssh session at you remote device, you can log into proot-distro to actually access and run the IIAB applications, just like at the installation you login using,

```
proot-distro login debian
```

There you'll be on a debian shell with access to the IIAB tools via CLI.

## Removal

If you want to remove the installation and remove all the related apps on it please follow the next steps.

1) Remove the IIAB installation running on `proot-distro` by running:

   ```
   proot-distro remove debian
   ```

   Please note that **all the content on that IIAB installation gets deleted by excecuting this command**. Backup your content properly if you want to install later on.

2) Remove / Uninstall Termux app

3) If applicable, Remove / Uninstall Shizuku app (Android 12/13)

4) Disable Developer options.

# proot-distro service manager (pdsm)

`pdsm` is a simple custom service implementation to manage services on a systemd like fashion on a Debian / Debian based distro on the Android port of IIAB.

## Usage

`pdsm` has a simple straight forward structure.

Starting a service is not the same as enable it. By *enabling* it, the service will start on every future session, *start* only will start on current session. Out of caution, only a handfull of services are actually enabled by default.

```
Usage: pdsm {enable-all|enable|disable|start|start-all|stop|restart|status|list} [service]
```

**TLDR**

If you want to start all services at once, you can do it by:

```
pdsm start-all
```

If you want to enable all services at once, you can do it by:
```
pdsm enable-all
```

### Examples

- pdsm list

  ```
  root@localhost:~# pdsm list
  [pdsm] available:
  calibre-web  kiwix  kolibri  nginx

  [pdsm] enabled:
  nginx
  ```

- pdsm enable-all

  ```
  root@localhost:~# pdsm enable-all
  [pdsm] enabled calibre-web
  [pdsm] enabled kiwix
  [pdsm] enabled kolibri
  [pdsm] enabled nginx


  root@localhost:~# pdsm list
  [pdsm] available:
  calibre-web  kiwix  kolibri  nginx

  [pdsm] enabled:
  calibre-web  kiwix  kolibri  nginx
  ```

- pdsm restart (service)

  ```
  root@localhost:~# pdsm restart calibre-web
  [pdsm:calibre-web] stopping...
  [pdsm:calibre-web] starting...
  ```

  Note: Out of caution due the Android resource consumption policies enabling a service doesn't automatically start it, but will start it on the following, equivalent to _"booting"_ which is, session login:

  ```
  ~ $ proot-distro login debian

  Published password in use by user 'iiab-admin'.
  THIS IS A SECURITY RISK - please run 'sudo passwd iiab-admin' to change it.

  [pdsm:calibre-web] running
  [pdsm:kiwix] running
  [pdsm:kolibri] running
  [pdsm:nginx] running
  root@localhost:~#
  ```

**Note**: The amount of services running cuncurrently is defined by the number of child processes allowed, whether via Developer Settings UI (Android 14+) or adb commands (Android 12 - 13).

If not setup propely, services will be stopped by the Phantom Process Killer ([learn more](https://github.com/agnostic-apollo/Android-Docs/blob/master/en/docs/apps/processes/phantom-cached-and-empty-processes.md)).

## Structure

As this is a custom implementation, it's set in `/usr/local` and the current tree of the package can be seen as follows:

```
pdsm/
├── etc_profile.d
│   └── pdsm.sh
├── pdsm-installer.sh
├── usr_local_bin
│   └── pdsm
└── usr_local_pdsm
    ├── lib
    │   └── pdsm-common.sh
    └── services-available
        ├── calibre-web
        ├── kiwix
        ├── kolibri
        ├── mariadb
        ├── nginx
        └── php-fpm

6 directories, 10 files
```

The installer sets the package in place, on the required directories,

- /etc/profile.d
- /usr/local/bin/
- /usr/local/pdsm
  - /usr/local/pdsm/lib
  - /usr/local/pdsm/services

## Future services

The service list should increase as needed by the supported apps on IIAB on Android / PRoot-Distro environment.
