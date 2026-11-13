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

`./runrole` applies one or more roles. It reads `/etc/iiab/local_vars.yml`.
An apply is repeatable: it installs a missing role, then configures an
installed role.

### Commands

    sudo ./runrole captiveportal                    # apply one role
    sudo ./runrole transmission kiwix               # apply several roles
    sudo ./runrole --add captiveportal              # apply despite captiveportal_install: False
    sudo ./runrole --reinstall awstats              # remove, then install again
    sudo ./runrole --upgrade <role>                 # upgrade, once the role ships upgrade.yml
    sudo ./runrole --uninstall awstats              # uninstall, never deleting user data
    sudo ./runrole --uninstall awstats --skip-never-installed  # ignore roles with no markers
    ./runrole --status captiveportal                # show installed and desired state
    ./runrole --list                                # list roles, state, conflicts, capabilities
    sudo ./runrole --check-local-vars               # validate local_vars.yml, then exit
    sudo ./runrole --log /tmp/iiab.log captiveportal

- `--reinstall` installs the role again. If the role ships `uninstall.yml`,
  `./runrole` first runs that file. It removes the program, its program data,
  its managed settings, and its declared user settings. The reinstall then
  installs the role and records its markers again. A reinstall never deletes
  user data. If the role has no `uninstall.yml`, the reinstall runs
  `install.yml` again and `./runrole` warns that the result is ambiguous. A
  role can refuse
  `--reinstall` with `reinstall: false` in
  `roles/<role>/meta/runrole.yml`; `kolibri`, `wordpress`, and `azuracast` do.
- For a legacy role, `./runrole` removes the state markers before the reinstall
  starts. A failed reinstall then leaves the role marked as uninstalled.
  `./iiab-install --reinstall` is different: it resets only the stage counter
  and reruns the stages. To reinstall one role, use
  `./runrole --reinstall <role>`.
- `--upgrade` upgrades an installed role through the program's own upgrade
  method. The role must ship `upgrade.yml` (or, for a legacy role, implement
  `when: upgrade`). No role ships `upgrade.yml` in 1.0. See "Upgrades" below.
- `--uninstall` removes the program, its program data, managed settings, and
  user settings. It never deletes user data. Only leaf roles support it; shared
  infrastructure roles do not. With several roles, `./runrole` refuses to start
  if any listed role has no installed marker. Add `--skip-never-installed` to
  uninstall the installed roles and report the others.
- `--continue-on-error` runs each role in a separate playbook and continues
  after a role fails. At the end, it reports the failed roles and exits
  nonzero. Without this option, the run stops at the first failure. It can be
  combined with `--uninstall`. A preflight failure stops the whole run before
  any role starts. Preflight failures include an unsupported operation and,
  for `--uninstall` or `--upgrade`, a missing marker. For an apply or a
  reinstall, `<app>_install: False` is also a preflight failure.
- `--status` and `--list` are read-only. `--check-local-vars` is also read-only;
  it validates only the listed roles or prefixes, or the full checklist when
  none are given. A listed prefix with no 0-init checklist entry is an error.
- `--log FILE` writes the Ansible log to FILE instead of `./iiab-debug.log`.
- `LOCAL_VARS_FILE`, `DEFAULT_VARS_FILE`, and `IIAB_STATE_FILE` override the
  local-vars, defaults, and state-file paths for the shell checks and the entry
  playbooks.
- Role lifecycle operations use internal `iiab_role_*` flags. Do not set them
  in `local_vars.yml`; use the CLI options.
- `./runroles` is a deprecated alias for `./runrole`; it accepts the same
  arguments.

`--uninstall` and `--reinstall` ask for confirmation before they remove
programs or reset settings. Pass `-y` in automation.

Capability detection uses one rule per operation. A legacy role supports
`--uninstall` or `--upgrade` when its entry point includes the phase file, has
an inline `when: uninstall` or `when: upgrade` path, or when
`meta/runrole.yml` declares `uninstall: true` or `upgrade: true`. A role that
uses the shared runner must ship `tasks/uninstall.yml` or `tasks/upgrade.yml`;
a manifest flag cannot add a phase. Every existing role supports `--reinstall`
unless `meta/runrole.yml` sets `reinstall: false`.

### Conflicts with the observed state

If a role is recorded as installed, an edit to `local_vars.yml` alone cannot
turn it off. Inspect the current state without a change:

    ./runrole --status squid
    ./runrole --list

Then do one of these actions:

- Keep the role: set `<prefix>_install: True` in `local_vars.yml`.
- Remove it, when the role supports `--uninstall`: run
  `sudo ./runrole --uninstall <role>`.
- Clear a stale marker: run `sudo ./scripts/iiab-state forget <prefix>`. Do
  this only after the program, its program data, and its settings are gone.

`--add` forces `<app>_install: True` for one run without an edit to
`local_vars.yml`.

## Role task lifecycle

A converted role is a role that uses the shared lifecycle runner. It uses a
fixed set of task files. `tasks/main.yml` only dispatches to the runner in
`roles/0-init/tasks/lifecycle.yml`:

    - name: Run the <Role> lifecycle
      include_role:
        name: 0-init
        tasks_from: lifecycle

| File | Runs when | Network access |
|---|---|---|
| `main.yml` | every invocation | no (it only dispatches) |
| `install.yml` | first install and `--reinstall` | yes |
| `upgrade.yml` | `--upgrade` only, instead of `install.yml` | yes |
| `configure.yml` | every apply | only to download a missing immutable asset |
| `state.yml` | after a successful apply | no |
| `uninstall.yml` | `--uninstall` and the remove half of `--reinstall` | no |

The runner starts these phases through `main.yml`. The phases can use the
network when the table permits it. `main.yml` itself must not.

`install.yml` is the only phase that installs the program. The runner starts it
on a first install and on `--reinstall`. It does not start it when an installed
role is applied. On `--upgrade`, `upgrade.yml` replaces it. Put work that must
run on every apply in `configure.yml`. `enable-or-disable.yml` is a
legacy convention that the runner still runs; `awstats` uses it for the NGINX
shortcut. Put new toggles in `configure.yml`.

- `upgrade.yml` is optional. It runs instead of `install.yml` on `--upgrade` and
  must use the program's own upgrade method. It must not write schema
  migrations or `local_vars.yml`. No role ships one in 1.0.
- `uninstall.yml` removes the program, its program data, managed settings, and
  declared user settings. It never deletes user data. Its final task removes
  the role's state markers. This file also supplies the remove half of
  `--reinstall`: put cleanup that a reinstall needs at the bottom of the file,
  before the markers are removed. If the role has no `uninstall.yml`,
  `--reinstall` runs `install.yml` again and `./runrole` warns that the result
  is ambiguous. Only leaf roles ship `uninstall.yml`. Shared infrastructure
  roles, such as `mysql`, `postgresql`, `mongodb`, `nginx`, `proot_services`,
  `sshd`, `www_base`, and `www_options`, do not.
- Write the installed marker only after configure succeeds. Normally,
  `state.yml` does this. Test a marker with `lookup('installed', 'mysql')`, not
  the `*_installed` variable.
- Do not add `disk_usage_start.yml` or `disk_usage_finish.yml` to a role that
  uses the runner. The runner measures disk use for the whole lifecycle.
- Notify `Reload nginx` when a role changes NGINX configuration. Use
  `Restart nginx` only when the role replaces the daemon itself. Both handlers
  are in `roles/0-init/handlers/main.yml`.

`awstats` is the reference implementation, including reinstall and uninstall.
To convert a role:

1. Replace `main.yml` with the include.
2. Move first-install work to `install.yml` and repeatable work to
   `configure.yml`.
3. Add `state.yml`.
4. Add `uninstall.yml` only if removal is safe. This file also supplies the
   remove half of `--reinstall`; put reinstall cleanup at its bottom.
5. Add `upgrade.yml` only if the program has its own upgrade method.
6. Run `python3 scripts/test-role-lifecycle.py <role>`.

If a reinstall is unsafe, set `reinstall: false` in
`roles/<role>/meta/runrole.yml` instead. A converted role does not run
`install.yml` when the role is already installed, so move repeatable work to
`configure.yml`.

The test uses mocked filesystems, services, and processes. It resolves a mocked
download to the fixture file shipped with the role, so `include_vars` on a
downloaded catalog sees the real content. `--strict` turns lifecycle warnings
into failures. `--all` tests every active role; `--jobs N` sets the
parallelism. Roles that do not use the shared runner fail the test, so `--all`
fails until the migration is complete.

## Data ownership

A converted role separates five classes of data and settings. Do not treat
"settings" as one class. The lifecycle uses these classes:

| Class | Contents | Apply to an installed role | `--reinstall` | `--uninstall` |
|---|---|---|---|---|
| **Program** | packages, binaries, source trees, service units | not changed | removed, then installed again | removed |
| **Program data** | generated config, caches, indexes, logs, generated service files | updated by `configure.yml` | removed by `uninstall.yml`, then recreated | removed |
| **Managed settings** | values set from `local_vars.yml` | set from `local_vars.yml` | set again | removed |
| **User settings** | app preferences and administrator choices, or hand-edited config that IIAB does not manage | not changed | removed by `uninstall.yml`, then created again from the shipped default | removed |
| **User data** | uploads, content, database records, generated reports | not changed | never deleted | never deleted |

This table describes a role that ships `uninstall.yml`. Without that file,
`--reinstall` runs `install.yml` again and does not reset user settings.

`local_vars.yml` is user input for managed settings. An apply enforces those
values. User settings are different: IIAB creates them once, then the user owns
them. If a role cannot keep the two apart in one file, split the file. Do not
overwrite the whole file.

For a user-setting file, create it only when it is missing and never overwrite
it:

    - name: Install the app configuration
      template:
        src: app.conf.j2
        dest: "{{ app_config_file }}"
        force: false

This rule preserves an existing user setting on an apply, and on `--reinstall`
when the role has no `uninstall.yml`. `--uninstall` removes the file. When
`uninstall.yml` removes it, the next apply creates the shipped default again.
`copy` and `template` support `force: false`; use it for user-setting files.
`lineinfile`, `blockinfile`, and `ini_file` have no `force` option. For those
modules, check whether the file, line, or key exists and skip the write, or
merge at the key level. Do not overwrite an existing value.

If a shipped default must change without discarding local edits, use a
three-way checksum check or a key-level merge. Do not overwrite
unconditionally.

Declare the paths that a role owns in `defaults/main.yml`. Use the role's
marker prefix (`calibre-web` uses `calibreweb_...`):

    exampleapp_user_settings:
      - /etc/exampleapp/settings.conf
    exampleapp_program_data:
      - /var/cache/exampleapp
    exampleapp_user_data:
      - /var/lib/exampleapp/uploads

A path belongs to exactly one class. The lifecycle test creates the declared
user settings and user data, then fails if any of these conditions is true:

- An apply changes a user setting.
- `--uninstall` does not remove a user setting.
- A role with `uninstall.yml` does not reset a user setting on `--reinstall`.
- An operation deletes user data.
- A path appears in more than one class.

`awstats` is the reference implementation: an apply preserves its user setting,
`--reinstall` resets it, and `--uninstall` removes it. Only `awstats` is
converted so far. A new conversion must declare ownership before the test can
prove it.

## Upgrades

`--upgrade` has a narrow scope. No role ships `upgrade.yml` in 1.0. An upgrade
must use the program's own method: back up the files that the program needs,
replace the program or package, and let the program migrate its own data on
startup. IIAB roles do not write schema migrations.

The scope is:

- A role offers `--upgrade` only when it ships `upgrade.yml`, or when a legacy
  role has an inline `when: upgrade` path. If detection cannot see an unusual
  implementation, the role can declare `upgrade: true` in
  `meta/runrole.yml`. Shared infrastructure roles do not offer `--upgrade`.
- Cross-OS-major upgrades are out of scope. Reinstall IIAB on the new OS. An OS
  upgrade can change database and package major versions.
- Keep long-lived pinned resources pinned in Ansible (`local_vars.yml` or the
  role defaults). The user updates the pin before the upgrade. `upgrade.yml`
  must not rewrite `local_vars.yml`.
- If a program has no upgrade method, its role does not ship `upgrade.yml`.

`--reinstall` is not `--upgrade`. A reinstall removes the role when
`uninstall.yml` exists, then installs it again. It resets user settings only in
that case. An upgrade keeps the installation and the user settings in place
while the program moves to the pinned version.

## Observed state

`/etc/iiab/iiab_state.yml` is a flat YAML mapping (`awstats_installed: True`).
This format keeps `vars_files`, `grep`, and image fixtures working. A missing
file is a valid empty state for the module, the lookup, and
`./scripts/iiab-state`. During the migration, the entry playbooks load the file
with `vars_files`, so `./runrole` creates it when it is missing. The path comes
from `iiab_state_file`; the default is `IIAB_STATE_FILE` or
`/etc/iiab/iiab_state.yml`.

Write a marker through the module, not `lineinfile`:

    - name: Record AWStats installed
      iiab_state:
        key: awstats_installed

Entry playbooks pass the path once with `module_defaults`. Shell code uses
`./scripts/iiab-state`:

    ./scripts/iiab-state get awstats_installed
    ./scripts/iiab-state is-installed awstats
    ./scripts/iiab-state forget awstats
    ./scripts/iiab-state diff expected.yml /etc/iiab/iiab_state.yml

`normalize` and `diff` compare only `_installed` and `_downloaded` markers.
They ignore comments, key order, `True`/`true` spelling, and unrelated keys.
The module, lookup plugin, and command use one parser. All writes use one code
path.

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
