## :world_map: IIAB on Android documentation map

This README documents the **`proot_services` role** (PRoot service management - systemd replacement scripts).

For the broader **"IIAB on Android"** overview and Android-side steps, see:

- **Overview + install guide:** https://github.com/iiab/iiab-android/blob/main/README.md
- **Termux setup details:** https://github.com/iiab/iiab-android/blob/main/termux-setup/README.md

# PRoot Distro service manager (pdsm)

`pdsm` is a simple custom service manager that provides systemd-like service management for Debian (or Debian-based) distributions in the Android port of IIAB.

## Usage

`pdsm` has a simple, straightforward structure.

Starting a service is not the same as enabling it. **Enabling** a service means it will start in every future session, while **starting** a service only affects the current session. Out of caution, only a handful of services are enabled by default.

```
Usage: pdsm {enable-all|enable|disable|start|start-all|stop|restart|status|list} [service]
```

**TL;DR**

To start all services at once:

```
pdsm start-all
```

To enable all services at once:

```
pdsm enable-all
```

### Examples

* `pdsm list`

  ```
  root@localhost:~# pdsm list
  [pdsm] available:
  calibre-web  kiwix  kolibri  nginx

  [pdsm] enabled:
  nginx
  ```

* `pdsm enable-all`

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

* `pdsm restart <service>`

  ```
  root@localhost:~# pdsm restart calibre-web
  [pdsm:calibre-web] stopping...
  [pdsm:calibre-web] starting...
  ```

  **Note:** Due to Android resource consumption policies, enabling a service does not automatically start it. Instead, it will start on the next session login (equivalent to “booting”):

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

**Note:** The number of services that can run concurrently is defined by the number of allowed child processes, either via the Developer Settings UI (Android 14+) or via ADB commands (Android 12–13).

If not set up properly, services may be stopped by the Phantom Process Killer ([learn more](https://github.com/agnostic-apollo/Android-Docs/blob/master/en/docs/apps/processes/phantom-cached-and-empty-processes.md)).

## Structure

Since this is a custom implementation, it is installed under `/usr/local`. The current package tree looks like this:

```
pdsm/
├── etc_profile.d
│   └── pdsm.sh
├── pdsm-installer.sh
├── usr_local_bin
│   └── pdsm
└── usr_local_pdsm
    ├── lib
    │   └── pdsm-common.sh
    └── services-available
        ├── calibre-web
        ├── kiwix
        ├── kolibri
        ├── mariadb
        ├── nginx
        └── php-fpm

6 directories, 10 files
```

The installer places files in the required directories:

* `/etc/profile.d`
* `/usr/local/bin`
* `/usr/local/pdsm`

  * `/usr/local/pdsm/lib`
  * `/usr/local/pdsm/services`

## Future services

The service list will expand as needed to support additional IIAB Apps on Android in the PRoot Distro environment.
