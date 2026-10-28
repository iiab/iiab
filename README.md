*Sharing the World's Free Knowledge*

# Internet-in-a-Box (IIAB)

[Internet-in-a-Box (IIAB)](https://internet-in-a-box.org) is a “learning hotspot” that brings the Internet's crown jewels
(Wikipedia in any language, thousands of Khan Academy videos, zoomable OpenStreetMap, electronic books, WordPress journaling, “Toys from Trash” electronics projects, ETC) to those without Internet.

You can build your own tiny, affordable server (an offline digital library) for your school, your medical clinic, your prison, your region and/or your very own family — accessible with any nearby smartphone, tablet or laptop.

Internet-in-a-Box gives you the DIY tools to:
1. Download then drag-and-drop to arrange the [very best of the World’s Free Knowledge](https://internet-in-a-box.org/#quality-content).
2. Choose among [30+ powerful educational apps](https://wiki.iiab.io/go/FAQ#What_services_%28IIAB_apps%29_are_suggested_during_installation%3F) for your school or learning/teaching community, optionally with a complete LMS (learning management system).
3. Exchange local/indigenous knowledge with nearby communities, using our [Manage Content](https://github.com/iiab/iiab-admin-console/blob/master/roles/console/files/help/InstContent.rst#manage-content) interface and possible mesh networking.

FYI this [community product](https://en.wikipedia.org/wiki/Internet-in-a-Box) is enabled by professional volunteers working [side-by-side](https://wiki.iiab.io/go/FAQ#What_are_the_best_places_for_community_support%3F) with schools, clinics and libraries around the world.  *Thank you for being a part of our http://OFF.NETWORK grassroots technology [movement](https://meta.wikimedia.org/wiki/Internet-in-a-Box)!*

## Installation

Install Internet-in-a-Box (IIAB) from: [**download.iiab.io**](https://download.iiab.io/)

Please see [FAQ.IIAB.IO](https://wiki.iiab.io/go/FAQ) which has 50+ questions and answers to help you along the way (e.g. [“Is a quick installation possible?”](https://wiki.iiab.io/go/FAQ#Is_a_quick_installation_possible%3F)) as you put together the <!--digital--> “local learning hotspot” most suitable for your own teaching/learning community.  Here are 2 ways to install IIAB:

- Our [1-line installer](https://download.iiab.io/) gets you the very latest, typically within about an hour, on [different Linux distributions](https://github.com/iiab/iiab/wiki/IIAB-Platforms#operating-systems).
- [Prefab disk images](https://github.com/iiab/iiab/wiki/Raspberry-Pi-Images-~-Summary#iiab-images-for-raspberry-pi) ([image files](https://github.com/iiab/iiab/releases)) can be flashed directly onto a microSD card, for insertion into Raspberry Pi.

Our [HOW-TO videos](https://www.youtube.com/channel/UC0cBGCxr_WPBPa3IqPVEe3g) can be very helpful and the [Installation](https://github.com/iiab/iiab/wiki/IIAB-Installation) wiki page has more intricate details e.g. if you're trying to install Internet-in-a-Box (IIAB) onto a [another Linux](https://github.com/iiab/iiab/wiki/IIAB-Platforms) that has not yet been tried.

See our [Tech Docs Wiki](https://github.com/iiab/iiab/wiki) for more about the underlying nuts and bolts.

After you've installed the software, you should [add content](https://github.com/iiab/iiab/wiki/IIAB-Installation#add-content), which can of course take time when downloading multi-gigabyte Content Packs!

Finally, you can [customize your Internet-in-a-Box home page](https://wiki.iiab.io/go/FAQ#How_do_I_customize_my_Internet-in-a-Box_home_page%3F) (typically http://box or http://box.lan) using our **drag-and-drop** Admin Console (http://box.lan/admin) &mdash; to arrange Content Packs and IIAB Apps (services) for your local community's needs.

## Running roles individually

`./runrole` applies one or more roles using `/etc/iiab/local_vars.yml`. Runs are
repeatable: each role is installed if missing and otherwise reconfigured.

    sudo ./runrole captiveportal                    # apply one role
    sudo ./runrole transmission kiwix               # apply several roles
    sudo ./runrole --add captiveportal              # apply despite captiveportal_install: False
    sudo ./runrole --reinstall captiveportal        # rebuild the program
    sudo ./runrole --clean-install awstats          # uninstall, then install again
    sudo ./runrole --uninstall awstats              # uninstall, never deleting user data
    sudo ./runrole --uninstall awstats --skip-missing  # ignore roles that are not installed
    ./runrole --status captiveportal                # show installed/desired state
    ./runrole --list                                # list roles, state, conflicts, capabilities
    sudo ./runrole --check-local-vars               # validate local_vars.yml, then exit
    sudo ./runrole --log /tmp/iiab.log captiveportal

- `--reinstall` reruns `install.yml` (installing first when missing). Converted
  roles keep their state markers and user settings until the rebuild succeeds;
  legacy roles have their markers removed first and offer no user-settings
  guarantee. A role can opt out with `reinstall: false` in
  `roles/<role>/meta/runrole.yml`.
- `--clean-install` is `--uninstall` followed by a fresh install, so it needs
  `--uninstall` support. It resets user settings and never deletes user data.
- `--uninstall` removes the program, its program data, and its user settings
  where supported. It never deletes user data. With several roles it refuses to
  start if any listed role is not installed; add `--skip-missing` to remove the
  installed roles and report the rest.
- `--status` and `--list` are read-only. `--check-local-vars` validates only
  the listed role(s)/prefix(es), or the full checklist when none are given.
- `--log FILE` writes the Ansible log to FILE instead of `./iiab-debug.log`.
- `./runroles` is a deprecated alias for `./runrole`; it accepts the same
  arguments.

Roles support `--uninstall` when `tasks/main.yml` implements it (an
`uninstall.yml` include, or inline `when: uninstall`). `meta/runrole.yml` can
override detection with `uninstall: true` / `reinstall: false`.

### Conflicts with the installed state

An app already recorded as installed cannot be turned off by editing
`local_vars.yml` alone. Inspect without changing anything:

    ./runrole --status squid
    ./runrole --list

Keep it, uninstall it where supported (`sudo ./runrole --uninstall <role>`), or
clear a stale marker with `sudo ./scripts/iiab-state forget <prefix>`. Clear a
marker only after the program and its settings are gone. `--add` forces
`<app>_install: True` for one run without editing `local_vars.yml`.

## Role task lifecycle

Converted roles keep a small, fixed set of task files; `tasks/main.yml` only
dispatches to the shared runner in `roles/0-init/tasks/lifecycle.yml`:

    - name: Run the <Role> lifecycle
      include_role:
        name: 0-init
        tasks_from: lifecycle

| File | Runs when | May use the network? |
|---|---|---|
| `main.yml` | every invocation | no (it only dispatches) |
| `install.yml` | first install, `--reinstall`, `--clean-install` | yes |
| `configure.yml` | every apply | only to fetch a missing immutable asset |
| `state.yml` | after a successful apply | no |
| `uninstall.yml` | `--uninstall` and `--clean-install` | no |

`main.yml` starts the phases below through the runner, so the `install.yml` it
may start can still use the network; `main.yml` itself must not.

`install.yml` is the only phase that installs or updates the program, and the
runner gates it: it does not run when applying an already-installed role.
Anything that must be reconciled every time belongs in `configure.yml`.
`enable-or-disable.yml` is a legacy convention the runner still executes; new
work belongs in `configure.yml`.

- `uninstall.yml` removes the program, its program data, and its declared user
  settings, never user data, and removes the role's state markers as its final
  task.
- Write the installed marker only after configure succeeds (normally in
  `state.yml`). Test markers with `lookup('installed', 'mysql')`, not the
  `*_installed` variable directly.
- Do not add `disk_usage_start.yml` / `disk_usage_finish.yml` to a role that
  uses the runner; it measures disk usage around the whole lifecycle.
- Prefer the shared `Reload nginx` / `Restart nginx` handlers in
  `roles/0-init/handlers/main.yml` over restarting NGINX in a role.

`awstats` is the reference implementation. To convert a role: replace
`main.yml` with the include, move first-install-only work to `install.yml` and
repeatable work to `configure.yml`, add `state.yml`, add `uninstall.yml` only if
removal is safe, then run `python3 scripts/test-role-lifecycle.py <role>`.
Converting a role stops
`install.yml` from running when applying an already-installed role, so move
re-applied work to `configure.yml`.

The test runs against mocked filesystems, services, and processes. Use
`--strict` to turn lifecycle warnings into failures, and `--all` to test every
active role (`--jobs N` sets its parallelism).

## Data ownership

A converted role distinguishes five kinds of state. "Settings" is not one
category, and the lifecycle must not treat it as one.

| Class | Examples | Apply (already installed) | `--reinstall` | `--uninstall` | `--clean-install` |
|---|---|---|---|---|---|
| **Program** | packages, binaries, source trees, service units | not touched | rebuilt | removed | removed and rebuilt |
| **Program data** | generated config, caches, indexes, logs, generated service files | reconciled by `configure.yml` | may be discarded and rebuilt | removed | removed and rebuilt |
| **Managed settings** | values driven by `local_vars.yml` | reconciled from `local_vars.yml` | reconciled | removed | reset from `local_vars.yml` |
| **User settings** | app-owned preferences and admin choices, or hand-edited config that IIAB does not manage | preserved | preserved | removed | reset |
| **User data** | uploads, content, database records, generated reports | untouched | untouched | never removed | never removed |

The `--reinstall` user-settings guarantee applies to converted roles using the
shared runner. Legacy roles keep their current behavior and offer no guarantee.

`local_vars.yml` is the user-owned *input* for managed settings; an apply
enforces it. User settings are the opposite: state the user owns after IIAB
seeds it. If a role cannot separate the two in one file, split the file rather
than overwriting the whole file.

The simple rule for a user-setting file is to create it only when missing and
never overwrite it:

    - name: Install the app configuration
      template:
        src: app.conf.j2
        dest: "{{ app_config_file }}"
        force: false

This preserves an existing user setting on apply and `--reinstall`.
`--uninstall` removes it; `--clean-install` then reseeds the shipped default.
Apply the same guard to `copy`, `lineinfile`, `ini_file`, and `blockinfile`:
do not write a user-setting file without it.

If a shipped default must change without discarding local edits, use a
three-way checksum check or a key-level merge; do not overwrite
unconditionally.

Declare what a role owns in `defaults/main.yml`, using the role's state-marker
prefix (`calibre-web` uses `calibreweb_...`):

    exampleapp_user_settings:
      - /etc/exampleapp/settings.conf
    exampleapp_program_data:
      - /var/cache/exampleapp
    exampleapp_user_data:
      - /var/lib/exampleapp/uploads

A path belongs to exactly one class. The lifecycle test seeds these paths and
fails if apply or `--reinstall` overwrites a user setting, `--uninstall` does
not remove it, `--clean-install` does not reset it, user data is deleted, or a
path appears in more than one class. The reinstall check covers converted
roles only.

`awstats` is the reference implementation: the user setting survives apply and
`--reinstall`, is removed by `--uninstall`, and is reset by `--clean-install`.
Only `awstats` is converted so far; new conversions must declare ownership
before the test can prove it.

## Observed state

`/etc/iiab/iiab_state.yml` remains a flat YAML mapping
(`awstats_installed: True`), so `vars_files`, `grep`, and image fixtures keep
working. A missing file is a valid empty state for the module, the lookup, and
`./scripts/iiab-state`; during the migration the entry playbooks still load it
with `vars_files`, so `./runrole` creates it when absent. The
path comes from `iiab_state_file`, which defaults to `IIAB_STATE_FILE` or
`/etc/iiab/iiab_state.yml`.

Write markers through the module, not `lineinfile`:

    - name: Record AWStats installed
      iiab_state:
        key: awstats_installed

Entry playbooks pass the path once with `module_defaults`. Shell code uses
`./scripts/iiab-state`:

    ./scripts/iiab-state get awstats_installed
    ./scripts/iiab-state is-installed awstats
    ./scripts/iiab-state forget awstats
    ./scripts/iiab-state diff expected.yml /etc/iiab/iiab_state.yml

`normalize`/`diff` ignore comments, key order, and `True`/`true` spelling. The
module, lookup plugin, and command share one parser and one write path.

## Community

Global community updates and videos are regularly posted to: **[@internet_in_box](https://twitter.com/internet_in_box)**

_Internet-in-a-Box (IIAB) greatly welcomes contributions from educators, librarians and [IT/UX/QA people](https://github.com/iiab/iiab/wiki/Contributors-Guide-(EN)) ([versión en español](https://github.com/iiab/iiab/wiki/Gu%C3%ADa-para-Contribuidores-(ES))) of all kinds!_

If you would like to volunteer, please [make contact](https://internet-in-a-box.org/contributing.html) after looking over [“How can I help?”](https://wiki.iiab.io/go/FAQ#How_can_I_help%3F) at: [FAQ.IIAB.IO](https://wiki.iiab.io/go/FAQ)

<!-- To learn about our software architecture, check out our [Contributors Guide](https://github.com/iiab/iiab/wiki/IIAB-Contributors-Guide).-->

To learn more about our open community architecture for “offline” learning, check out [“What technical documentation exists?”](https://wiki.iiab.io/go/FAQ#What_technical_documentation_exists%3F)
FYI we use [Ansible](https://wiki.iiab.io/go/FAQ#What_is_Ansible_and_what_version_should_I_use%3F) <!--as the underlying technology--> to install, deploy, configure and manage the various software components.

*Thank you for helping us enable offline access to the Internet's free/open knowledge jewels, as well as “Sneakernet-of-Alexandria” distribution of local/indigenous content, when mass media channels do not serve grassroots voices.*

## Versions

Pre-releases of Internet-in-a-Box (IIAB) undergo continuous QA / continuous integration / continuous deployment and are **strongly recommended!**

Install our latest pre-release using the 1-line installer at: [**download.iiab.io**](https://download.iiab.io/)

You can also consider <!--latest Internet-in-a-Box (IIAB)--> earlier official releases at: [github.com/iiab/iiab/releases](https://github.com/iiab/iiab/releases)

For much older versions, see: [github.com/xsce](https://github.com/xsce)
