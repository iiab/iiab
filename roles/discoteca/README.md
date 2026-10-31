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

## Databases and media

Databases live in `{{ discoteca_data_dir }}` (`/library/discoteca` by default),
which is user data: `--uninstall` and `--reinstall` never delete it. The role
creates a missing database as an empty SQLite file, but does not scan media.

To add a library, create or fill a database with the `disco` command:

    sudo -u discoteca disco add /library/discoteca/audio.db /library/audio
    sudo -u discoteca disco add /library/discoteca/books.db /library/books

Then list every database the service should serve:

    discoteca_databases:
      - "{{ discoteca_data_dir }}/library.db"
      - "{{ discoteca_data_dir }}/audio.db"
      - "{{ discoteca_data_dir }}/books.db"

and apply the role again. Each database path must already be an existing file;
the role creates an empty one if it is missing.

Media directories only need to be readable by the `discoteca` user. The systemd
unit keeps the filesystem read-only except the home and database directories.

## Variables

| Variable | Default | Purpose |
|---|---|---|
| `discoteca_version` | `latest` | Release to install; pin an X.Y.Z value for reproducibility. |
| `discoteca_url` | `/disco` | NGINX URL prefix. |
| `discoteca_port` | `5555` | Loopback port. |
| `discoteca_databases` | `/library/discoteca/library.db` | Databases to serve. |
| `discoteca_db_cache_mb` | `64` | SQLite page cache per connection. |
| `discoteca_max_concurrent_searches` | `2` | Concurrent `/api/query` searches. |
| `discoteca_read_only` | `false` | Refuse progress updates, playlists, and deletions. |
| `discoteca_packages` | `[ffmpeg]` | Optional runtime packages (transcoding, HLS). |
| `discoteca_memory_high` / `discoteca_memory_max` | `70%` / `80%` | Service cgroup memory limits. |

Upstream publishes `linux-amd64` and `linux-arm64` binaries. 32-bit ARM
(armv7/armv6) is not released yet, so the install fails clearly on those hosts.

## Lifecycle behavior

- **Apply** installs a missing role, then runs `configure.yml` on every apply.
  It never overwrites an existing database.
- **`--reinstall`** removes the program, home directory, unit, and NGINX
  configuration, then installs and configures again. Databases and media stay.
- **`--uninstall`** removes the program, home directory, unit, and NGINX
  configuration. Databases and media stay.
- **`--upgrade`** is not shipped; `--reinstall` swaps the binary and restarts
  the service. Back up databases before a major version change.
