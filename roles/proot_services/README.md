# Internet-in-a-Box on Android

Internet-in-a-Box (IIAB) on Android means that millions of people worldwide can build their own family libraries, inside their own phones.

As of January 2026, these IIAB Apps are supported:

* Calibre-Web
* Kiwix
* Kolibri
* Maps
* Matomo

The default port for the web server is **8085**, for example:

```
http://localhost:8085/maps
```

## Installation

1. Install **Termux**:

   * OPTION 1: Directly install Termux, using a recent .apk file: [https://github.com/Termux/Termux-app/releases/](https://github.com/Termux/Termux-app/releases/) ("universal" .apk file GENERALLY BEST)
   * OPTION 2: Install Termux from the [F-Droid app store](https://f-droid.org/packages/com.termux/) (no Google account needed)
   * OPTION 3: Install Termux from the [Google Play Store](https://play.google.com/store/apps/details?id=com.termux) (often problematic, avoid if possible)

   Warning: If you use either app store above, please bear in mind Termux developers' advice against mixing Termux app / plugins from different stores.

2. Enable **Developer Options** on Android:

   * In **Settings > About phone** (sometimes in **Software information**), find the **Build number**, and tap it seven times rapidly!

3. Remove or increase the app child process limit to install and run IIAB:

   * On Android 14 and later, it is possible to disable this restriction using Android Settings, in **Developer Options**, with this setting:

     * `Disable child process restrictions` (English), or
     * `Desactivar restricciones de procesos secundarios` (Spanish)

   * Android 12 and 13 added a ["Phantom Process Killer" (PPK)](https://github.com/agnostic-apollo/Android-Docs/blob/master/en/docs/apps/processes/phantom-cached-and-empty-processes.md) feature to limit child processes, but there is no UI option to disable this behavior on those versions. Instead, you can disable it using ADB commands issued from a remote device, or locally on the device using **[Shizuku](https://github.com/RikkaApps/Shizuku/releases/)**.

     Shizuku is a 3-step process: **Pair**, **Run**, and **Export**. Please check this (WIP) [video tutorial](https://ark.switnet.org/tmp/termux-shizuku-a12-setup_light.mp4) for a more interactive explanation. Once exported, the `0_termux_setup.sh` script (just below) will handle the PPK workaround setup.

4. Prepare the Termux app by running the following command from the Termux terminal:

   ```
   curl https://raw.githubusercontent.com/iiab/iiab/refs/heads/master/roles/proot_services/0_termux-setup.sh | bash
   ```

   Once complete, enter the Debian environment to continue the installation:

   ```
   proot-distro login debian
   ```

5. Run the `1_iiab-on-android.sh` script which (a) installs `local_vars_android.yml` to [`/etc/iiab/local_vars.yml`](https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it?) and (b) runs the IIAB installer:

   ```
   curl https://raw.githubusercontent.com/iiab/iiab/refs/heads/master/roles/proot_services/1_iiab-on-android.sh | bash
   ```

   If the installer completes successfully, the installation process is finished.
   If you encounter an error or problem, please open an [issue](https://github.com/iiab/iiab/issues) so we can help you (and others) as quickly as possible.

## Remote Access

While using the phone keyboard and screen is practical when on the move, accessing the PRoot Distro environment from a PC or laptop is very useful for debugging. You can use an existing Wi-Fi connection or enable the native Android hotspot if no wireless LAN is available.

Get your phone’s IP address by running `ifconfig` in Termux or by checking **About device → Status** in Android settings.

### SSH

To log in to IIAB on Android from your computer, follow these SSH (command-line interface) instructions:

1. Set up SSH credentials (on Termux, not PRoot Distro).

   The fastest way to SSH into your Android phone (or tablet) is to set a password for its Termux user. In Termux (not PRoot Distro), run:

   ```
   passwd
   ```

   To determine the Termux username, run:

   ```
   whoami
   ```

   Optionally, security can be improved by using standard SSH key-based authentication via the `~/.ssh/authorized_keys` file.

2. Start the SSH service from Termux: (not PRoot Distro)

   ```
   sshd
   ```

   The `sshd` service can be automated to start when Termux launches (see [Termux-services](https://wiki.Termux.com/wiki/Termux-services)). We recommend doing this only after improving login security using SSH keys.

3. SSH to your Android phone.

   From your laptop or PC, connected to the same network as your Android phone, and knowing the phone’s IP address (e.g., `192.168.10.100`), run:

   ```
   ssh -p 8022 192.168.10.100
   ```

   No specific username is required. Note that port **8022** is used for SSH.

   Since Android runs without root permissions, SSH cannot use lower-numbered ports. For the same reason, the IIAB web server (nginx) uses port **8085** instead of port 80.

### Log in to the IIAB environment

Once you have an SSH session on your remote device, log into PRoot Distro to access and run the IIAB applications, just as during installation:

```
proot-distro login debian
```

You will then be in a Debian shell with access to the IIAB CLI (command-line interface) tools.

## Removal

If you want to remove the installation and all related apps, follow these steps:

1. Remove the IIAB installation running in PRoot Distro:

   ```
   proot-distro remove debian
   ```

   **Note:** All content in that IIAB installation will be deleted when executing this command. Back up your content first if you plan to reinstall later.

2. Remove / uninstall the Termux app.

3. If applicable, remove / uninstall the Shizuku app (Android 12–13).

4. Disable Developer Options.

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
