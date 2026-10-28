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

`./runrole` applies one role using `/etc/iiab/local_vars.yml`. Runs are
repeatable: the role is installed if missing and otherwise reconfigured.
`install.yml` owns installing and updating the program, so there is no separate
`--upgrade` flag.

    sudo ./runrole captiveportal                    # apply
    sudo ./runrole --add captiveportal              # apply despite captiveportal_install: False
    sudo ./runrole --reinstall captiveportal        # rebuild the program
    sudo ./runrole --clean-install awstats          # uninstall, then install again
    sudo ./runrole --uninstall awstats              # uninstall, never deleting user data
    ./runrole --status captiveportal                # show installed/desired state
    ./runrole --list                                # list roles, state, conflicts, capabilities
    sudo ./runrole --check captiveportal            # best-effort dry run
    sudo ./runrole --check-local-vars               # validate local_vars.yml, then exit

The options escalate, from least to most work:

- `--reinstall` reruns the role's install/update path. A role whose rebuild
  needs manual cleanup can opt out with `reinstall: false` in
  `roles/<role>/meta/runrole.yml`.
- `--clean-install` is literally `--uninstall` followed by a normal apply, so
  it requires the role to support `--uninstall`.
- `--uninstall` removes the program and its settings where supported.

No runrole option deletes user data. Roles declare it in `<role>_user_data`
(and `<role>_user_data_databases`); the lifecycle test checks every operation
against those declarations. Remove user data manually if you really need to.

`--reinstall` is a rebuild, not a reset. Whether existing program data and
settings survive depends on the role. Use `--clean-install` when you want a
known clean slate. `--uninstall` keeps the role's state marker until
`uninstall.yml` removes it as its final task, so a failed uninstall can be
retried.

Roles are converted to the lifecycle runner one at a time. Until a role is
converted, it keeps its previous apply and reinstall behavior; `--reinstall`
only guarantees that `install.yml` reruns for converted roles.

`./runroles` accepts the same options and multiple roles, e.g.
`./runroles --status captiveportal kiwix`.

`runrole` and `runroles` validate only the role(s) they were asked to run. Full
installs validate the complete 0-init checklist. `--check-local-vars` validates
configuration only, is read-only, and does not run role-specific runtime checks.

If `./runrole --uninstall <role>` keeps failing, fix the reported error and
retry. If you already removed the program another way, clear its markers with
the role's state-file prefix (not always its directory name):

    sudo ./scripts/iiab-state forget --dry-run awstats
    sudo ./scripts/iiab-state forget awstats

Only do that after the program and its settings are gone.

### If local_vars.yml conflicts with the installed state

The most common error after a failed install is setting `<app>_install: False`
for an app that IIAB already recorded as installed. Inspect the state without
changing anything:

    ./runrole --status squid
    ./runrole --list

Then keep the app, uninstall it where supported
(`sudo ./runrole --uninstall <role>`), or clear a stale marker with
`sudo ./scripts/iiab-state forget <state-prefix>`. The last step is only safe
after the program and its settings are gone. `--add` forces `<app>_install:
True` for one run without editing `local_vars.yml`.

### Role capabilities

A role supports `--uninstall` when its `tasks/main.yml` implements it
(`tasks/uninstall.yml`, a hand-off to it, or an inline `when: uninstall`).
`--clean-install` is supported by exactly the same roles. `--reinstall` is
available to roles that have not opted out. `--status` reports the capabilities
detected for a role, and `--list` shows them for every role.

For unusual roles whose implementation cannot be detected from their tasks, an
optional `roles/<role>/meta/runrole.yml` can opt in or out:

    ---
    uninstall: true
    reinstall: false

Role names, state-marker prefixes (`calibre-web` -> `calibreweb`), install/
enabled prefixes (`iiab-admin` -> `admin_console`), and capability detection
live in `scripts/role_lifecycle.py`, which both the shell tools and
`scripts/test-role-lifecycle.py` call. Ansible task files reach the marker map
through `lookup_plugins/role_var.py`. Helper roles that never have their own
`*_install` switch (`firmware`, `pylibs`, `www_base`, `www_options`) are
declared in `NO_INSTALL_PREFIX`.

## Role task lifecycle

Roles that adopt the safe-apply pattern keep a small, fixed set of task files so
a maintainer can decide where a change belongs without guessing.
`tasks/main.yml` does not repeat the phase order: it includes the shared runner
in `roles/0-init/tasks/lifecycle.yml`:

    - name: Run the <Role> lifecycle
      include_role:
        name: 0-init
        tasks_from: lifecycle

The runner identifies the calling role, looks up its state-marker prefix with
`lookup('role_var', ...)`, discovers which phase files exist, and runs them in
order. It also handles the `--uninstall` guard, the `--reinstall` guard, the
install-state snapshot, disk measurement, and the `skip_role_on_error` rescue.
Add role-specific work before or after the include, or move it into the phase
file it belongs to. `awstats` is the reference implementation; `matomo` and
`transmission` follow in later pull requests.

The central rule is: **`install.yml` is gated by the runner**. It runs on the
first install, during `--reinstall`, and during the apply half of
`--clean-install`. It does **not** run on an ordinary apply of an already
installed role. Put anything that must be reconciled on every apply in
`configure.yml` (or in `enable-or-disable.yml` / `state.yml` when that is the
natural home).

| File | Required? | Runs when | May use the network? |
|---|---|---|---|
| `main.yml` | yes | every invocation; normally only includes the runner | no |
| `validate.yml` | optional | every apply except `--uninstall` | no |
| `install.yml` | optional | first install, `--reinstall`, and the apply half of `--clean-install` | yes (install/update only) |
| `configure.yml` | optional | every apply | only to fetch a missing immutable asset |
| `enable-or-disable.yml` | optional | every apply | no |
| `state.yml` | optional | after a successful apply | no |
| `reinstall.yml` | optional | `--reinstall` only | no |
| `uninstall.yml` | optional | `--uninstall` and the uninstall half of `--clean-install` | no |

The rules are intentionally simple:

- `install.yml` is the only phase that installs or updates the program and its
  packages. Because the runner gates it, first-install-only work (cloning,
  moving an existing tree aside, unconditional downloads) is safe.
- `configure.yml` reconciles desired state on every run. Move settings,
  templates, database provisioning and service configuration here when they
  must be re-applied on an ordinary apply.
- `reinstall.yml` only stops the service and removes directories that are safe
  to rebuild. It never removes declared user data. `--clean-install` does not
  run it.
- `uninstall.yml` removes the program and its settings, never declared user
  data, and removes the role's state markers as its final task.
- Write the installed marker only after `configure.yml` (and any
  enable/disable step) has succeeded. Roles that use the runner do this in
  `state.yml`. Never write it in `install.yml` or a helper included by it.
- Do not add `disk_usage_start.yml` / `disk_usage_finish.yml` includes to a
  role that uses the shared runner. The runner measures disk usage around the
  whole `install.yml` -> `configure.yml` sequence when the role is not
  installed yet or is being reinstalled, and writes the delta to `iiab.ini`.
- Put computed values in `vars/main.yml`, user-facing knobs in
  `defaults/main.yml`, and service restarts in `handlers/main.yml`.
- A role that only adds or removes an NGINX config file should notify the
  shared `Reload nginx` / `Restart nginx` handlers in
  `roles/0-init/handlers/main.yml` instead of restarting NGINX itself. Add
  `meta: flush_handlers` only if a later task needs the new configuration live
  immediately.
- `*_installed` and `*_downloaded` markers are observed state, not
  configuration. Never test one directly. Use the `installed` lookup
  (`lookup_plugins/installed.py`) for every check, including the install gate:

      when: not lookup('installed', 'mysql') or reinstall

  The state file is no longer loaded through `vars_files`; the lookup reads it
  directly and also sees a marker set with `set_fact` earlier in the run.

### Converting an existing role

1. Replace the body of `main.yml` with the lifecycle include above.
2. Move first-install-only work to `install.yml`; move work that must be
   reconciled on every apply to `configure.yml`.
3. Add `state.yml` to record `iiab.ini` values and write the installed marker
   through `iiab_state`.
4. Add `uninstall.yml` only if removal is safe and repeatable. Add
   `reinstall.yml` only if a rebuild needs local cleanup.
5. Declare user data in `defaults/main.yml`.
6. Run `python3 scripts/test-role-lifecycle.py <role>`.

**Behavior changes to call out in review:** converting a role stops
`install.yml` from running on an ordinary apply of an already-installed host.
Anything that used to be re-applied from `install.yml` must move to
`configure.yml` or it will only run again on `--reinstall`/`--clean-install`.
Conversely, `--reinstall` now actually reruns `install.yml` for converted
roles, so a rebuild that used to be silently skipped will now happen.

## Observed state

`/etc/iiab/iiab_state.yml` remains a flat YAML mapping
(`awstats_installed: True`), so `vars_files`, existing `grep` checks, and image
fixtures keep working. A missing file is a valid empty state. The path comes
from `iiab_state_file`, which defaults to `IIAB_STATE_FILE` or
`/etc/iiab/iiab_state.yml`.

Write a marker through the module instead of `lineinfile`:

    - name: Record AWStats installed
      iiab_state:
        key: awstats_installed

    - name: Forget AWStats markers
      iiab_state:
        key: awstats_installed
        state: absent

Entry playbooks pass the path once with `module_defaults`:

    module_defaults:
      iiab_state:
        path: "{{ iiab_state_file }}"

Shell code uses `./scripts/iiab-state` instead of editing the file with
`grep`/`sed`:

    ./scripts/iiab-state get awstats_installed
    ./scripts/iiab-state is-installed awstats
    ./scripts/iiab-state forget awstats
    ./scripts/iiab-state diff expected.yml /etc/iiab/iiab_state.yml

`normalize` and `diff` ignore comments, key order, and `True`/`true` spelling.
The module, lookup plugin, and command share one parser and one locked, atomic
write path, so concurrent writers cannot lose each other's markers.

## User data

A role that owns user data declares what it must not delete while reinstalling,
clean-installing, or uninstalling. Put the list in `defaults/main.yml`:

    # transmission/defaults/main.yml
    transmission_user_data:
      - "{{ transmission_download_dir }}"

A role whose user data lives in a database declares the database names
separately:

    # matomo/defaults/main.yml
    matomo_user_data: []
    matomo_user_data_databases:
      - "{{ matomo_db_name }}"

Use the role's state-file prefix, so `calibre-web` uses `calibreweb_user_data`.
`--clean-install`, `--reinstall`, and `--uninstall` must leave every declared
path and database in place. There is no option that deletes them.

`scripts/test-role-lifecycle.py` also scans the lifecycle task files and prints
`WARN` lines with the file, line, and task name when a phase that must work
offline does network work, when an offline phase includes a phase that may use
the network, or when a state marker is tested directly. Warnings do not fail
unless `--strict` is used. A deliberate exception can carry a
`# lifecycle: allow-network <reason>` comment immediately above the task.

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
