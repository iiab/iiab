=============
Zimantic
=============

Zimantic provides meaning-based, title-word, and native ZIM full-text search,
plus direct article serving from local ZIM archives.

This role is opt-in. It does not replace ``kiwix-serve`` by default because
Zimantic needs Python 3.11-3.14, compatible native dependencies, and more disk
space for its Python environment. ``libzim`` publishes wheels only for specific
Python versions, so select ``zimantic_python`` only after confirming that a
compatible wheel exists. On 32-bit ``armhf`` hosts, where no wheels are
published, the role installs the native dependencies from Debian 13/trixie or
newer instead. Existing IIAB Kiwix URLs and the Kiwix Android APK remain
unchanged by default.

Configuration
-------------

Set these variables in ``/etc/iiab/local_vars.yml`` and run the role.

Fast mode
~~~~~~~~~

``fast`` is the default and needs no embedding model. Set::

    zimantic_install: True
    zimantic_enabled: True
    zimantic_mode: fast

Fast mode uses about 66 MiB RSS with one small ZIM. It provides ZIM-native
full-text search and title-word search once a fast index has been built.
Zimantic opens every archive under ``zimantic_zim_dir``, so RSS grows with the
number and size of ZIMs. A test with 761 archives used about 646 MiB RSS; on a
Pi Zero 2 W, point ``zimantic_zim_dir`` at a small set of ZIMs rather than the
full IIAB library. The server is available at ``http://box/zimantic`` through
NGINX. It also listens on ``http://box:8090/`` for troubleshooting and direct
access from the LAN (see the firewall note under "Relationship to Kiwix").

Semantic mode
~~~~~~~~~~~~~

``semantic`` adds meaning-based search. The role downloads the selected
embedding model when it is missing. Set::

    zimantic_install: True
    zimantic_enabled: True
    zimantic_mode: semantic

The semantic server uses about 323 MiB RSS with ``multilingual-e5-small``;
``e5-small-v2`` uses less. 64-bit ``aarch64`` and ``x86_64`` hosts use the PyPI
wheels. 32-bit ``armhf``/``armv7`` hosts have no wheels, so by default the role
installs ``python3-onnxruntime``, ``python3-faiss``, ``python3-libzim``,
``python3-sentencepiece``, and the other native dependencies as distribution
packages, then creates the virtual environment with ``--system-site-packages``.
This requires Debian 13/trixie or newer.

Embedding model
~~~~~~~~~~~~~~~

Choose the model by uncommenting one block in
``roles/zimantic/defaults/main.yml`` and commenting out the other, or copy the
chosen block into ``/etc/iiab/local_vars.yml``:

- ``multilingual-e5-small`` (default) is about 123 MiB and searches 100+
  languages.
- ``e5-small-v2`` is about 34 MiB, English only, and saves roughly 125 MiB of
  resident memory. It is the better choice on hosts with 1 GB RAM or less.

Each block sets ``zimantic_embedding_model``, the model URL and checksum, and
the tokenizer file, URL, and checksum. Indexes are specific to the model that
built them, so rebuild them after switching (``zimantic build --force``).

Native dependencies
~~~~~~~~~~~~~~~~~~~

``zimantic_use_system_packages`` controls where native dependencies come from:

- ``auto`` (default) uses PyPI wheels on 64-bit hosts and distribution
  packages on ``armhf``/``armv7``.
- ``always`` uses distribution packages on every architecture and therefore
  requires Debian 13/trixie or newer.
- ``never`` always uses PyPI wheels. This fails on ``armhf``/``armv7`` because
  no wheels are published.

Indexes
~~~~~~~

The role does not build indexes. Build a fast (title and full-text) index
during a maintenance window::

    cd /library/zimantic && sudo -u zimantic /opt/iiab/zimantic/.venv/bin/zimantic build --fast

A full semantic index build can be expensive on small devices, so the role does
not attempt it. Build semantic indexes on a faster compatible machine, copy the
files into ``/library/zimantic/indexes``, and restart the service. When memory
is limited, set ``zimantic_zim_dir`` to a directory containing only the archives
you want searched; the default is IIAB's complete ``/library/zims/content``.

Memory and restart limits
~~~~~~~~~~~~~~~~~~~~~~~~~

The systemd unit puts Zimantic in its own cgroup. ``zimantic_memory_high``
(default ``70%``) makes the kernel reclaim and throttle under pressure, and
``zimantic_memory_max`` (default ``80%``) is the hard limit: exceeding it
OOM-kills Zimantic inside its cgroup instead of letting the whole device run
out of memory. ``zimantic_oom_score_adjust`` (default ``200``) only makes
Zimantic a preferred victim during a system-wide OOM; by itself it does not cap
memory. On a 512 MB host, 80% leaves roughly 100 MB for the kernel, NGINX,
Kiwix and SSH, so lower both percentages or point ``zimantic_zim_dir`` at a
smaller set of archives if other services are starved.

If Zimantic is OOM-killed, systemd retries after ``zimantic_restart_sec``
(default 10 seconds). After ``zimantic_start_limit_burst`` starts in
``zimantic_start_limit_interval`` (default three in ten minutes), it leaves the
unit failed instead of restarting into another OOM. Check ``systemctl status
zimantic`` and ``journalctl -u zimantic``; after fixing the cause,
``systemctl reset-failed zimantic`` clears the rate limit so the service can be
started again before the interval expires.

Task layout
-----------

The role follows the shared role lifecycle described in the top-level
``README.md``:

- ``update.yml`` fetches ``zimantic_version`` and installs missing system
  packages. It runs on first install, version changes, ``--upgrade``,
  ``--force-reinstall``, or when the checkout is missing or does not match
  ``zimantic_version``.
- ``install.yml`` creates the virtual environment and rebuilds the Python
  package from the local checkout. It uses ``--no-deps`` for a normal repair or
  ``--reinstall``, so those paths work offline when the checkout and virtual
  environment already exist.
- ``configure.yml`` runs on every apply and reconciles the user, directories,
  model files, ``config.toml``, and the systemd unit.
- ``reinstall.yml`` only stops the service and performs the
  ``--force-reinstall`` deletions; it never downloads anything.
- ``install.yml`` writes the installed/version marker as soon as the build
  succeeds, so a later configure failure does not force another dependency
  resolution on an offline host. ``state.yml`` reports the settings in
  ``iiab.ini``.

Derived values (the selected embedding model and the decision to update) live in
``vars/main.yml``. Service restarts are handlers, so the task files only signal
what changed instead of carrying restart conditions.

Upgrading
---------

``./runrole zimantic`` is the normal command. It checks out
``zimantic_version``, reinstalls the Python package when the checkout changes,
re-templates the configuration and systemd unit, and restarts the service only
when something changed. After pulling a newer IIAB revision, run::

    cd /opt/iiab/iiab
    git pull
    sudo ./runrole zimantic

A normal run that only repairs an already-installed version (for example a
missing executable) leaves dependencies alone, so it can run offline. A
checkout that does not match ``zimantic_version`` is fetched again, and
changing ``zimantic_version`` re-resolves dependencies; both normally need
network access.

Start with the normal apply. If that is not enough, escalate from least to most
work::

    sudo ./runrole --reinstall zimantic        # rebuild the program only
    sudo ./runrole --upgrade zimantic          # rebuild the program and dependencies
    sudo ./runrole --force-reinstall zimantic  # also reset source, settings, indexes, and model
    sudo ./runrole --uninstall zimantic        # remove the service, data, and settings
    ./runrole --status zimantic                # show installed/desired state

``--reinstall`` rebuilds only the Python package from the local checkout. It
keeps the virtual environment, dependencies, data, indexes, and settings, and
can run offline when the checkout already matches ``zimantic_version``.

``--upgrade`` rebuilds the Python package and re-resolves its dependencies from
the current checkout. Use it after changing ``zimantic_version`` or when
dependencies need updating; it normally requires network access.

``--force-reinstall`` also deletes ``zimantic_source_dir`` and
``zimantic_data_dir`` (indexes, model, and ``config.toml``), so the role
rebuilds everything from scratch. In ``semantic`` mode it downloads the model
again, so it also requires network access.

``--uninstall`` stops and disables the service, removes its systemd unit and
NGINX shortcut, deletes ``zimantic_source_dir`` and ``zimantic_data_dir``, and
removes the ``zimantic`` user. Set ``zimantic_install: False`` (and
``zimantic_enabled: False``) in ``local_vars.yml`` to keep it uninstalled.

``--reinstall``, ``--force-reinstall``, and ``--uninstall`` require an existing
``zimantic`` entry in ``/etc/iiab/iiab_state.yml``. ``--force-reinstall`` and
``--uninstall`` ask for ``yes`` unless ``-y`` is given; ``--reinstall`` does not
prompt. ``--reinstall``, ``--upgrade``, and ``--force-reinstall`` also require
``zimantic_install: True``; pass ``--add`` if you intentionally disabled it.
``--status`` is read-only and cannot be combined with the other options.

The role declares these extended operations in
``roles/zimantic/meta/runrole.yml``. ``./runrole`` refuses ``--uninstall``,
``--upgrade``, or ``--force-reinstall`` for roles that do not declare them, so
the flags fail before an unsupported role can change anything.

The source checkout under ``zimantic_source_dir`` is disposable: the role
discards local tracked changes when checking out the requested version. Runtime
data, indexes, and models live under ``zimantic_data_dir``. Changing
``zimantic_mode`` rewrites the configuration and systemd unit and restarts the
service. Switching to ``semantic`` downloads the model if it is missing, and a
semantic build upgrades a ``fast`` index in place.

To reset manually instead, stop the service, remove both directories, and rerun
the role::

    sudo systemctl stop zimantic
    sudo rm -rf /library/zimantic /opt/iiab/zimantic

``zimantic_version`` may be a git tag or a commit hash. pip reports the
package version from Zimantic's ``pyproject.toml``, so the package version and
the checked-out revision do not need to match. A commit hash is useful before
a release is tagged; the commit must be reachable from ``zimantic_repo`` (push
it, or point ``zimantic_repo`` at a local checkout). If pip reports an older
package version, use a corrected Zimantic tag or release rather than editing
``pyproject.toml`` on the device.

Relationship to Kiwix
---------------------

The role reads ``/library/zims/content`` directly and does not need
``kiwix-serve`` for local results. Kiwix remains useful for its existing
library catalog and Android app. To use Zimantic instead of ``kiwix-serve``,
set::

    kiwix_enabled: False
    zimantic_install: True
    zimantic_enabled: True

Zimantic continues to use its default port 8090 and URL
``http://box/zimantic``. NGINX proxies the URL to the local service, so
blocking the direct port does not affect ``http://box/zimantic``. Like other
IIAB apps, the installer opens port 8090 on the WAN side only when
``ports_externally_visible`` is 3 or higher; lower that setting (or block 8090
yourself) to keep the direct port reachable only from the LAN. Port 8090 may
collide with AzuraCast's container port range or the deprecated httpd role;
override ``zimantic_port`` if needed. When ``kiwix_enabled: False`` and
``zimantic_enabled: True``, ``http://box/kiwix`` and ``/kiwix/`` also redirect
to Zimantic. Disabling Kiwix stops and disables ``kiwix-serve``, removes its
Nginx shortcut, and removes its scheduled restart; it does not uninstall an
existing Kiwix installation. Keep ``kiwix_install: True`` when using the IIAB
Admin Console, which requires the Kiwix role to be installed. The Kiwix
Android APK setting is separate.
