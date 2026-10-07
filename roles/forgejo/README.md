# Forgejo README

This Ansible role installs Forgejo — a self-hosted Git service written in Go
(a community-driven fork of Gitea). It is meant to host and distribute code and
knowledge offline, and runs both on systemd platforms (x86_64 / arm64) and under
proot (Android / Termux, via PDSM).

## Using It

Forgejo should be accessible at: http://box/forgejo

Repositories can be cloned over HTTP everywhere, and over SSH on systemd
platforms. HTTP clone URLs start with `http://box.lan/forgejo/`. On systemd, SSH
clone URLs start with `forgejo@box.lan` and use **port 2222** — Forgejo's own
built-in SSH server, not the host's `sshd`. Under proot, Forgejo is **HTTP-only**
(no built-in SSH).

**The first user account you register becomes the administrator.** The web
"install" screen is skipped (`INSTALL_LOCK` is enabled with the recommended
settings already applied), so the first time you open Forgejo you go straight to
registering that first — admin — user.

## Installation and Setup

Forgejo is **enabled on the `large` install size** — it ships turned on in
`vars/local_vars_large.yml`, so a large install (and the IIAB CI run for that
size) provisions it automatically. On smaller sizes it is off by default; turn it
on in `/etc/iiab/local_vars.yml`:

```yaml
forgejo_install: True
forgejo_enabled: True
```

Then run `cd /opt/iiab/iiab` and `sudo ./runrole forgejo`. After it finishes,
Forgejo is live at http://box/forgejo — register the first user to get the admin
account.

## Updating

The version is pinned (`forgejo_version`). To update, bump `forgejo_version`
(in `defaults/main.yml` or `local_vars.yml`) and run:

```sh
sudo ./runrole --reinstall forgejo
```

`--reinstall` is the update path. The role takes a backup (`forgejo dump`)
**before** swapping the binary, never touches your data (repositories + database),
and removes the superseded binary afterwards so disk use stays bounded.

## Configuration

Key variables live in `roles/forgejo/defaults/main.yml`:

- **`forgejo_port`** (default **3300**) — the local port Forgejo listens on;
  nginx reverse-proxies `http://box/forgejo` to it. 3300 is used (not Forgejo's
  default 3000) to avoid clashing with Kiwix under proot.

- **`forgejo_db_engine`** (default **sqlite**) — unlike the Gitea role, this role
  **wires the database backend for you**. Set it to `mariadb` to run on MariaDB:
  the role includes the `mysql` role, creates the database and user, and points
  Forgejo at it (under proot, MariaDB runs via PDSM). SQLite is the default and
  is recommended for most installs — the database stores only metadata, so repo
  size is irrelevant to the DB choice.

  > **The engine cannot be switched on an existing install.** The role refuses a
  > `sqlite` ↔ `mariadb` change (there is no automatic data migration between
  > engines); migrate manually with dump/restore if you really need to — see the
  > notes in `defaults/main.yml`.

- **`forgejo_ssh_port`** (default **2222**) — the built-in SSH server port on
  systemd. 2222 (not 22) keeps Forgejo clear of the host `sshd` and lets it
  coexist with the Gitea role on the same box.

- **`forgejo_enable_ssh`** (default: **on** for systemd, **off** under proot) —
  Forgejo's built-in SSH server. proot installs are HTTP-only by design.

- **`forgejo_migrate_timeout`** (default **7200**) — the `[git.timeout] MIGRATE`
  value, raised so large repository imports do not hit Forgejo's 600s default.
  The nginx `proxy_read_timeout` / `proxy_send_timeout` are derived from it.

To change any setting **before** the first install, edit the templates/defaults
rather than the live files:

- app.ini: `roles/forgejo/templates/app.ini.j2`
- systemd unit: `roles/forgejo/templates/forgejo.service.j2`
- nginx: `roles/forgejo/templates/forgejo-nginx.conf.j2`

Secrets (`SECRET_KEY`, `INTERNAL_TOKEN`, LFS JWT) are generated once and
referenced from `app.ini` by `*_URI` file paths, not stored in the template.

## Platforms

- **systemd (x86_64 / arm64):** full support, including the built-in SSH server.
- **proot (Android / Termux, via PDSM):** HTTP only. On a 32-bit userland over a
  kernel older than 5.1, the Go binary needs a proot with the `futex_time64` fix
  to run.

## Documentation

- Forgejo docs: <https://forgejo.org/docs/>
- IIAB role discussion: [iiab/iiab#4505](https://github.com/iiab/iiab/pull/4505)
