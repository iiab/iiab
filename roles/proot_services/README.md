# Internet-in-a-Box on Android

[Internet-in-a-Box (IIAB)](https://internet-in-a-box.org) on Android means that millions of people worldwide can build their own family libraries, inside their own phones.

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

Start with an Android 12-or-higher phone or tablet:

1. Install **Termux**:

   * OPTION 1: Directly install Termux, using a recent `.apk` file: [https://github.com/Termux/Termux-app/releases/](https://github.com/Termux/Termux-app/releases/) ("universal" `.apk` file GENERALLY BEST)
   * OPTION 2: Install Termux from the [F-Droid app store](https://f-droid.org/packages/com.termux/) (no Google account needed)
   * OPTION 3: Install Termux from the [Google Play Store](https://play.google.com/store/apps/details?id=com.termux) (often problematic, avoid if possible)

   Warning: If you use either app store above, please bear in mind Termux developers' advice against mixing Termux app / plugins from different stores.

2. Enable **Developer Options** on Android:

   * In **Settings > About phone** (sometimes in **Software information**), find the **Build number**, and tap it seven times rapidly!

3. Remove or increase the app child process limit to install and run IIAB:

   * On Android 14 and later, disable this restriction using Android Settings, in **Developer Options**:

     * `Disable child process restrictions` (English), or
     * `Desactivar restricciones de procesos secundarios` (Spanish)

   * Android 12 and 13 added a ["Phantom Process Killer" (PPK)](https://github.com/agnostic-apollo/Android-Docs/blob/master/en/docs/apps/processes/phantom-cached-and-empty-processes.md) feature to limit child processes, but there is no UI option to disable this behavior on those versions. Instead, you need to disable it using ADB commands issued from a remote device, or locally on the device using **[Shizuku](https://github.com/RikkaApps/Shizuku/releases/)**.

     Shizuku is a 3-step process: **Pair**, **Run**, and **Export**. Please check this (WIP) [video tutorial](https://ark.switnet.org/tmp/termux-shizuku-a12-setup_light.mp4) for a more interactive explanation. Once exported, the `0_termux_setup.sh` script (just below) will handle the PPK workaround setup.

4. Prepare the Termux app by running the following command from the Termux CLI (command-line interface):

   ```
   curl https://raw.githubusercontent.com/deldesir/iiab/refs/heads/master/roles/proot_services/0_termux-setup.sh | bash
   ```

   Once complete, enter [PRoot Distro](https://wiki.termux.com/wiki/PRoot)'s Debian environment to continue the installation:

   ```
   proot-distro login debian
   ```

5. Run the `1_iiab-on-android.sh` script which (a) installs `local_vars_android.yml` to [`/etc/iiab/local_vars.yml`](https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it?) and (b) runs the IIAB installer:

   ```
   curl https://raw.githubusercontent.com/deldesir/iiab/refs/heads/master/roles/proot_services/1_iiab-on-android.sh | bash
   ```

   **Customizing Installation:**
   If you want to edit `local_vars.yml` before the installation starts (e.g., to enable extra services), you can use the `IIAB_PAUSE_BEFORE_INSTALL` environment variable:
   ```bash
   curl https://raw.githubusercontent.com/deldesir/iiab/refs/heads/master/roles/proot_services/1_iiab-on-android.sh | IIAB_PAUSE_BEFORE_INSTALL=true bash
   ```
   The script will download the configuration and wait for you to edit `/etc/iiab/local_vars.yml` before proceeding.

   If the installer completes successfully, the installation process is finished. And you'll see a text box reading:

   > INTERNET-IN-A-BOX (IIAB) SOFTWARE INSTALL IS COMPLETE

## Test your IIAB install

Test your IIAB install by running the `pdsm` command as follows: ([learn more](https://github.com/deldesir/iiab/tree/master/roles/proot_services#proot-distro-service-manager-pdsm))

```
pdsm start-all
```

Then check that your IIAB Apps are working (using a browser on your Android device) by visiting these URLs:

| App                    | URL                                                            |
|------------------------|----------------------------------------------------------------|
| Calibre-Web            | [http://localhost:8085/books](http://localhost:8085/books)     |
| Kiwix (for ZIM files!) | [http://localhost:8085/kiwix](http://localhost:8085/kiwix)     |
| Kolibri                | [http://localhost:8085/kolibri](http://localhost:8085/kolibri) |
| IIAB Maps              | [http://localhost:8085/maps](http://localhost:8085/maps)       |
| Matomo                 | [http://localhost:8085/matomo](http://localhost:8085/matomo)   |

If you encounter an error or problem, please open an [issue](https://github.com/iiab/iiab/issues) so we can help you (and others) as quickly as possible.

### Add a ZIM file

A copy of Wikipedia (in almost any language) can now be put on your Android phone or tablet! Here's how...

1. Browse to website: [download.kiwix.org/zim](https://download.kiwix.org/zim/)
2. Pick a `.zim` file (ZIM file) and copy its full URL, for example:

   ``` 
   https://download.kiwix.org/zim/wikipedia/wikipedia_en_100_maxi_2025-10.zim
   ```

3. Open Android's Termux app, and then run:

   ```
   proot-distro login debian
   ```

   EXPLANATION: Starting from Termux's high-level CLI (Command-Line Interface), you've "shelled into" [PRoot Distro](https://wiki.termux.com/wiki/PRoot)'s low-level Debian CLI:

   ```
      +----------------------------------+
      |   Android GUI (Apps, Settings)   |
      +----------------+-----------------+
                       |
              open the | Termux app
                       v
      +----------------+-----------------+
      |       Termux (Android CLI)       |
      | $ proot-distro login debian      |
      +----------------+-----------------+
                       |
      "shell into" the | low-level environment
                       v
      +----------------+-----------------+
      | proot-distro: Debian (userspace) |
      | debian root# cd /opt/iiab/iiab   |
      +----------------------------------+
   ```

4. Enter the folder where IIAB stores ZIM files:

   ```
   cd /library/zims/content/
   ```

5. Download the ZIM file, using the URL you chose above, for example:

   ```
   wget https://download.kiwix.org/zim/wikipedia/wikipedia_en_100_maxi_2025-10.zim
   ```

6. Once the download is complete, re-index your IIAB's ZIM files: (so the new ZIM file appears for users, on page http://localhost:8085/kiwix)

   ```
   iiab-make-kiwix-lib
   ```

   TIP: Repeat this last step whenever removing or adding new ZIM files from `/library/zims/content/`

## Remote Access

While using the phone keyboard and screen is practical when on the move, accessing the PRoot Distro's Debian environment from a PC or laptop is very useful for debugging. You can use an existing Wi-Fi connection or enable the native Android hotspot if no wireless LAN is available.

Before you begin, obtain your Android phone or tablet’s IP address by running `ifconfig` in Termux. Or obtain the IP by checking **About device → Status** in Android settings.

### SSH

To log in to IIAB on Android from your computer, follow these SSH command-line interface (CLI) instructions:

1. On your Android phone or tablet, find your way to Termux's CLI. **If you earlier ran `proot-distro login debian` to get to PRoot Distro's low-level Debian CLI — you MUST step back up to Termux's high-level CLI — e.g. by running:**

   ```
   exit
   ```

2. The fastest way to SSH into your Android phone (or tablet) is to set a password for its Termux user. In Termux's high-level CLI, run:

   ```
   passwd
   ```

   Optionally, security can be improved by using standard SSH key-based authentication via the `~/.ssh/authorized_keys` file.

3. Start the SSH service. In Termux's high-level CLI, run:

   ```
   sshd
   ```

   The `sshd` service can be automated to start when Termux launches (see [Termux-services](https://wiki.Termux.com/wiki/Termux-services)). We recommend doing this only after improving login security using SSH keys.

4. SSH to your Android phone.

   From your laptop or PC, connected to the same network as your Android phone, and knowing the phone’s IP address (for example, `192.168.10.100`), you would run:

   ```
   ssh -p 8022 192.168.10.100
   ```

   A username is NOT needed!

   Note that port **8022** is used for SSH. Since Android runs without root permissions, SSH cannot use lower-numbered ports. (For the same reason, the IIAB web server [nginx] uses port **8085** instead of port 80.)

### Log in to the IIAB environment

Once you have an SSH session on your remote device, log into PRoot Distro to access and run the IIAB applications, just as during installation:

```
proot-distro login debian
```

You will then be in a Debian shell with access to the IIAB CLI (command-line interface) tools.

## Removal

If you want to remove the IIAB installation and all associated apps, follow these steps:

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
