# Internet in a Box on Android

Internet in a Box on Android benefits from the ubiquity of Android smartphones in all the world to reach new communities around the world.

This effort is on it's launching stage so only a limited of apps are supported.

- Caliber-Web
- Kiwix
- Kolibri
- Maps
- Matomo

The default port for the web server is **8085**, for example:

     http://localhost:8085/maps

## Installation

1) You are required to install **Termux**

- https://github.com/termux/termux-app/releases/

2) Enable **Developer Options** on Android.

3) Remove / increase app child processes limit to install and run IIAB.

- Android 14+  
    On Android 14 and later, it is possible to disable this restriction throught the UI on one *Developer options* setting called:
    - `Disable child process restriction`  (English) or
    - `Desactivar restricciones de procesos secundarios` (Spanish)

- Android 12-13  
  Since version 12+ Android added a new feature to limit child processes (PPK), there is no UI interface to modify such feature on 12 or 13. Then it requires to be modified via ADB commands, it can be done via:

    - using a PC to check current PPK value & increase Phantom Process Killer from current value (e.g. 32) to 256+

    ```
    adb shell "dumpsys activity settings | grep -i phantom" && \
    adb shell "device_config put activity_manager max_phantom_processes 256"  && \
    adb shell "dumpsys activity settings | grep -i phantom"
    ```

    - or whitin the same device by using **[Shizuku](https://github.com/RikkaApps/Shizuku/releases/)** check the documentation for how to acomplish it.  

    ```
    dumpsys activity settings | grep -i phantom && \
    device_config put activity_manager max_phantom_processes 256  && \
    dumpsys activity settings | grep -i phantom
    ```

4) Prepare termux-app, use the following command from the termux terminal.

```
curl -s https://github.com/iiab/iiab/blob/master/roles/proot_servirces/0_termux-setup.sh | bash
```
Once complete please enter the debian environment to continue the installation:

```
proot-distro login debian
```

5) Install the android local_vars and run the installer in order to install the current setup.

Once on the proot-distro environment you can install IIAB running the following script.
```
curl -s https://github.com/iiab/iiab/blob/master/roles/proot_servirces/1_iiab-on-android.sh | bash
```

If the installer completes correclty you have finished the installation process.  
If you find any error or issue, please help us by opening an [issue](https://github.com/iiab/iiab/issues) to track it and get it fixed in the shortest time possible.

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

**TLDR;**

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

If not setup propely, services will be stoped by the Phantom Process Killer ([learn more...](https://github.com/agnostic-apollo/Android-Docs/blob/master/en/docs/apps/processes/phantom-cached-and-empty-processes.md)).

## Structure

As this is a custom implementation it's set on /usr/local and current tree of the package can be seen as following:

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
