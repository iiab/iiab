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

Upstream publishes only a `linux-amd64` binary, and the newest release
(`v0.0.37`) predates the `--host`/`--base-path` flags this role needs. On arm64
Android (the usual case) the install builds from source with the Go toolchain
(`CGO_ENABLED=1`, tag `fts5`); when the latest release is too old it also builds
from source on amd64. This needs network access during install and takes a few
minutes on a phone.

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

Then list every database the service should serve:

    discoteca_databases:
      - "{{ discoteca_database_dir }}/library.db"
      - "{{ discoteca_database_dir }}/audio.db"
      - "{{ discoteca_database_dir }}/books.db"

and apply the role again. Each database path must already be an existing file;
the role creates an empty one if it is missing.

Media directories only need to be readable by the `discoteca` user. The
service's effective group is `www-data`, matching Kolibri and the rest of
`/library`; the systemd unit keeps the filesystem read-only except the home and
database directories. Back up `/library/discoteca` (the databases); media can
live anywhere and is only referenced by path.

## Reusing Calibre-Web content

If Calibre-Web is installed, its books and IIAB video downloads already live
under `{{ calibreweb_home }}` (`/library/calibre-web`). Discoteca indexes files
in place, so there is no need to copy them. Scan that tree into a discoteca DB:

    sudo -u discoteca disco add /library/discoteca/library.db /library/calibre-web \
      --ext .epub,.pdf,.mobi,.azw3,.mp4,.mkv,.webm,.mp3,.m4a,.flac,.ogg

The DB stays in `/library/discoteca`; Calibre-Web's own `metadata.db` and
`xklb-metadata.db` stay untouched, and its files are already readable by the
`discoteca` user through the shared `www-data` group. Add image extensions to
`--ext` (or drop `--ext` and add `--exclude 'cover.*'`) if you also want cover
images.

Do **not** point discoteca at `xklb-metadata.db` directly. Discoteca's schema
migration drops xklb-only columns (`webpath`, `extractor_id`, `time_uploaded`)
that Calibre-Web's uploader reads. To seed a separate discoteca DB from it,
stop Calibre-Web and copy the file first, then serve the copy.

## Variables

| Variable | Default | Purpose |
|---|---|---|
| `discoteca_version` | `latest` | Release to install; pin an X.Y.Z value for reproducibility. |
| `discoteca_build_from_source` | `false` | Force a Go source build even when a prebuilt binary exists. |
| `discoteca_source_ref` | `main` | Branch, tag, or commit built when using source. |
| `discoteca_url` | `/disco` | NGINX URL prefix. |
| `discoteca_port` | `5555` | Loopback port. |
| `discoteca_databases` | `/library/discoteca/library.db` | Databases to serve. |
| `discoteca_db_cache_mb` | `64` | SQLite page cache per connection. |
| `discoteca_max_concurrent_searches` | `2` | Concurrent `/api/query` searches. |
| `discoteca_read_only` | `false` | Refuse progress updates, playlists, and deletions. |
| `discoteca_packages` | `[ffmpeg]` | Optional runtime packages (transcoding, HLS). |
| `discoteca_group` | `www-data` | Effective group for the service and its files. |
| `discoteca_memory_high` / `discoteca_memory_max` | `70%` / `80%` | systemd cgroup memory limits (ignored under proot). |

The install uses the SHA-256 digest that GitHub reports for the release asset.
When no prebuilt asset exists for the host CPU (today: arm64), it builds
`discoteca_source_ref` from source. 32-bit x86 has no upstream build and no Go
mapping, so the install fails clearly instead of guessing.

## Lifecycle behavior

- **Apply** installs a missing role, then runs `configure.yml` on every apply.
  It never overwrites an existing database.
- **`--reinstall`** removes the program, home directory, unit, and NGINX
  configuration, then installs and configures again. Databases and media stay.
- **`--uninstall`** removes the program, home directory, unit, and NGINX
  configuration. Databases and media stay.
- **`--upgrade`** is not shipped; `--reinstall` swaps the binary and restarts
  the service. Back up databases before a major version change.
