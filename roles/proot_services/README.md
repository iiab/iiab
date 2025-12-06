# PRoot Services or proot-distro service manager(pdsm)

`pdsm` is a simple service implementation to manage services closely to what you would expect from a systemd like fashion on a Debian / Debian based distro.

## Usage

`pdsm` has a simple straight forward structure.

```
Usage: pdsm {enable-all|enable|disable|start|stop|restart|status|list} [service]
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

Note: The amount of services running cuncurrently is defined by the number of child processes allowed, whether via Developer Settings UI (Android 15+) or adb commands (Android 12 - 14).

If not setup propely, services will be stoped by the Phantom Process Killer ([learn more...](https://github.com/agnostic-apollo/Android-Docs/blob/master/en/docs/apps/processes/phantom-cached-and-empty-processes.md)).

## Structure

As this is a custom implementation it's set on /usr/local and current tree of the package can be seen as following:

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
        └── nginx

6 directories, 8 files
```

The installer sets the package in place, on the required directories,

- /etc/profile.d
- /usr/local/bin/
- /usr/local/pdsm
  - /usr/local/pdsm/lib
  - /usr/local/pdsm/services

## Future services

The service list should increase as needed by the supported apps on IIAB on Android / PRoot-Distro environment.
