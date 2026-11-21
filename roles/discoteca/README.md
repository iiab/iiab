# discoteca

[discoteca](https://github.com/chapmanjacobd/discoteca) is a local media
library and streaming server for offline video, audio, books, and images. It
serves one or more SQLite databases through an embedded web client, optionally
below an NGINX URL prefix.

This role uses the shared lifecycle runner in `roles/0-init/tasks/lifecycle.yml`,
so it supports `--reinstall` and `--uninstall` through `./runrole`.

## Enable

Add this to `/etc/iiab/local_vars.yml`:

    discoteca_install: True
    discoteca_enabled: True

Then run:

    sudo ./runrole discoteca

The web UI is at `http://box/disco/`. The service listens on `127.0.0.1:5555`
and NGINX proxies it.

## Android / proot

The role runs under Android's proot-distro with `proot_services` (pdsm), which
replaces systemd. Start from an Android local_vars file (`is_proot: True`), set:

    proot_services_install: True
    discoteca_install: True
    discoteca_enabled: True

then apply the roles:

    sudo ./runrole proot_services discoteca

The pdsm wrapper is shipped by `proot_services`
(`pdsm_installed_services`), and `discoteca` reads
`/etc/discoteca/serve.conf` and `/etc/discoteca/databases`. Manage it with:

    pdsm enable discoteca
    pdsm start discoteca
    pdsm status discoteca
    pdsm restart discoteca
    pdsm stop discoteca
    pdsm disable discoteca

pdsm logs to `/var/lib/discoteca/discoteca.log`. Like Kolibri, the service runs
as the unprivileged `discoteca` user with effective group `www-data` on both
systemd and proot, so the same `sudo -u discoteca disco add ...` command works
everywhere.

Release `v0.1.1` and newer ship `linux-amd64` and `linux-arm64` binaries with
GitHub-reported SHA-256 digests. The role installs the matching asset, so arm64
Android (the usual case) and amd64 use a prebuilt binary. CPUs without a release
asset, currently armv7 and armv6, build from source with the Go toolchain
(`CGO_ENABLED=1`, tag `fts5`); that needs network access during install and takes
a few minutes on a phone. Releases older than `v0.1.1` are refused.

`discoteca_source_ref` selects the source revision (`main` by default). Pin a
commit or a release tag for a reproducible image. Set
`discoteca_build_from_source: true` to force a source build on any
architecture.

## Databases and media

Databases live in `{{ discoteca_database_dir }}` (`/library/discoteca` by default),
which is user data: `--uninstall` and `--reinstall` never delete it. The role
creates a missing database as an empty SQLite file, but does not scan media.

To add a library, create or fill a database with the `disco` command:

    sudo -u discoteca disco add /library/discoteca/audio.db /library/audio
    sudo -u discoteca disco add /library/discoteca/books.db /library/books

Calibre libraries are better imported with `disco calibre-import`, which reads
Calibre's `metadata.db` (and optionally probes video/audio metadata) instead of
scanning a directory tree. See "Reusing Calibre-Web content" below.

Then list every database the service should serve:

    discoteca_databases:
      - "{{ discoteca_database_dir }}/library.db"
      - "{{ discoteca_database_dir }}/audio.db"
      - "{{ discoteca_database_dir }}/books.db"

and apply the role again. Each database path must already be an existing file;
the role creates an empty one if it is missing.

Media directories only need to be readable by the `discoteca` user. The
service's effective group is `www-data`, matching Kolibri and the rest of
`/library`; the systemd unit keeps the filesystem read-only except the home,
database, and download directories. Back up `/library/discoteca` (the databases)
and `/library/downloads/discoteca` (URL downloads); media can live anywhere and
is only referenced by path.

## Reusing Calibre-Web content

If Calibre-Web is installed, its books and IIAB video downloads already live
under `{{ calibreweb_home }}` (`/library/calibre-web`). Discoteca indexes files
in place, so there is no need to copy them. Import Calibre's catalog into a
discoteca DB:

    sudo -u discoteca disco calibre-import /library/discoteca/library.db \
      --calibre-web-dir /library/calibre-web/config

`--calibre-web-dir` is the directory containing Calibre-Web's `app.db`
(`calibreweb_config`, not `calibreweb_home`); it reads `config_calibre_dir` from
that database, then imports the formats recorded in Calibre's `metadata.db`.
`ffprobe` (from `discoteca_packages: [ffmpeg]`) fills duration and codecs for
video and audio; disable that with `--probe-media=false`. Useful options include
`--one-format` (only the highest-priority format per book), `--format-priority`,
`--prune` (mark books removed from Calibre as deleted), and `--include-missing`.

The DB stays in `/library/discoteca`; Calibre-Web's own `metadata.db` and
`xklb-metadata.db` stay untouched, and its files are already readable by the
`discoteca` user through the shared `www-data` group. To also index non-Calibre
media under that tree, union a `disco add` scan into the same or another
database:

    sudo -u discoteca disco add /library/discoteca/media.db /library/calibre-web \
      --ext .mp4,.mkv,.webm,.mp3,.m4a,.flac,.ogg

Calibre-Web's uploader stores its own catalog in `xklb-metadata.db`. Do **not**
point discoteca at that file directly: discoteca's schema migration drops
xklb-only columns (`webpath`, `extractor_id`, `time_uploaded`) that the uploader
reads. To seed a separate discoteca DB from it, stop Calibre-Web and copy the
file first, then serve the copy.

## URL downloads

The web UI can download a pasted `http(s)` URL and import it into the selected
database. Upstream uses `lb`, or `lb-wrapper` when `lb` is unavailable. IIAB's
Calibre-Web role installs those only when its audio/video support is enabled;
on other installs, downloads stay disabled until `lb` (or a compatible command)
is in `PATH` or `discoteca_download_command` names one. The command must be
executable by the `discoteca` user: IIAB links `/usr/local/bin/lb` into
`/root/.local/bin`, which the service user cannot traverse, so install `library`
somewhere the service can read it before enabling downloads.

Files are written to `discoteca_download_dir`
(`/library/downloads/discoteca` by default), which the role creates, owns as
`discoteca:www-data`, and never deletes. `discoteca_read_only` disables
downloads along with other write operations.

## ZIM files

ZIM support is off by default. Discoteca proxies an externally managed ZIM
server and never starts or stops it. `kiwix-serve` must be started with
`--urlRootLocation` matching the discoteca proxy route, for example
`--urlRootLocation=/disco/api/zim/proxy/` when `discoteca_url: /disco`; IIAB's
own `kiwix-serve` uses `/kiwix/`, so it cannot be reused without changing that
unit. Point discoteca at it in `/etc/iiab/local_vars.yml`:

    discoteca_kiwix_host: 127.0.0.1
    discoteca_kiwix_port: 8181

The newer `zimantic` backend needs no `urlRootLocation`: set its
`web_base_path = "/disco/api/zim/proxy"` in `~/.config/zimantic/config.toml`,
then set a positive port. It overrides `kiwix-serve` when both are configured:

    discoteca_zimantic_host: 127.0.0.1
    discoteca_zimantic_port: 8090

The ZIM file must also appear in one of `discoteca_databases`; discoteca
rejects files that are not listed. With neither server configured, ZIM routes
return `503`.

## Variables

| Variable | Default | Purpose |
|---|---|---|
| `discoteca_version` | `latest` | Release to install; must be `0.1.1` or newer. Pin an X.Y.Z value for reproducibility. |
| `discoteca_build_from_source` | `false` | Force a Go source build even when a prebuilt binary exists. |
| `discoteca_source_ref` | `main` | Branch, tag, or commit built when using source. |
| `discoteca_url` | `/disco` | NGINX URL prefix. |
| `discoteca_port` | `5555` | Loopback port. |
| `discoteca_databases` | `/library/discoteca/library.db` | Databases to serve. |
| `discoteca_download_command` | `auto` | Downloader (`lb`, `lb-wrapper`, or a command); `auto` disables downloads when neither is installed. |
| `discoteca_download_dir` | `/library/downloads/discoteca` | Writable destination for URL downloads. |
| `discoteca_db_cache_mb` | `64` | SQLite page cache per connection. |
| `discoteca_max_concurrent_searches` | `2` | Concurrent `/api/query` searches. |
| `discoteca_kiwix_port` | `0` | External kiwix-serve port; `0` disables. |
| `discoteca_zimantic_port` | `0` | External zimantic port; positive values override kiwix-serve. |
| `discoteca_read_only` | `false` | Refuse progress updates, playlists, downloads, and deletions. |
| `discoteca_packages` | `[ffmpeg]` | Optional runtime packages (transcoding, HLS, calibre-import probing). |
| `discoteca_group` | `www-data` | Effective group for the service and its files. |
| `discoteca_memory_high` / `discoteca_memory_max` | `70%` / `80%` | systemd cgroup memory limits (ignored under proot). |

The install uses the SHA-256 digest that GitHub reports for the release asset.
When this CPU has no release asset (currently armv7 and armv6), it builds
`discoteca_source_ref` from source. 32-bit x86 has no upstream build and no Go
mapping, so the install fails clearly instead of guessing.

## Lifecycle behavior

- **Apply** installs a missing role, then runs `configure.yml` on every apply.
  It never overwrites an existing database.
- **`--reinstall`** removes the program, home directory, unit, and NGINX
  configuration, then installs and configures again. Databases, downloads, and
  media stay.
- **`--uninstall`** removes the program, home directory, unit, and NGINX
  configuration. Databases, downloads, and media stay.
- **`--upgrade`** is not shipped; `--reinstall` swaps the binary and restarts
  the service. Back up databases before a major version change.
