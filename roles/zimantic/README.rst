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
access.

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

``zimantic_embedding_model`` selects the model:

- ``auto`` (default) uses ``e5-small-v2`` on hosts with 1 GB RAM or less and
  ``multilingual-e5-small`` otherwise.
- ``multilingual-e5-small`` is about 123 MiB and searches 100+ languages.
- ``e5-small-v2`` is about 34 MiB, English only, and saves roughly 125 MiB of
  resident memory.

Indexes are specific to the model that built them, so rebuild them after
changing ``zimantic_embedding_model`` (``zimantic build --force``).

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

Upgrading
---------

``./runrole zimantic`` is the normal command. It checks out
``zimantic_version``, reinstalls the Python package when the checkout changes,
re-templates the configuration and systemd unit, and restarts the service only
when something changed. After pulling a newer IIAB revision, run::

    cd /opt/iiab/iiab
    git pull
    sudo ./runrole zimantic

A normal run that only repairs an already-installed version (a missing
executable or a reset checkout) leaves dependencies alone, so it can run
offline. Changing ``zimantic_version`` re-resolves dependencies and normally
needs network access.

Start with the normal apply. If that is not enough, escalate from least to most
work::

    sudo ./runrole --reinstall zimantic        # rebuild the program only
    sudo ./runrole --upgrade zimantic          # rebuild the program and dependencies
    sudo ./runrole --force-reinstall zimantic  # also reset source, settings, indexes, and model
    sudo ./runrole --status zimantic           # show installed/desired state

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

``--reinstall`` and ``--force-reinstall`` require an existing ``zimantic`` entry
in ``/etc/iiab/iiab_state.yml``. ``--force-reinstall`` asks for ``yes`` unless
``-y`` is given; ``--reinstall`` does not prompt.

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

``zimantic_version`` is a git tag; pip reports the package version from
Zimantic's ``pyproject.toml``. The values should match without editing the
checkout. If pip reports an older version, use a corrected Zimantic tag or
release rather than editing ``pyproject.toml`` on the device.

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
``http://box/zimantic``. NGINX proxies the URL to the loopback service, so the
direct port can be firewalled while the application remains available through
the main IIAB HTTP port. When ``kiwix_enabled: False`` and
``zimantic_enabled: True``, ``http://box/kiwix`` and ``/kiwix/`` also redirect
to Zimantic. Disabling Kiwix stops and disables ``kiwix-serve``, removes its
Nginx shortcut, and removes its scheduled restart; it does not uninstall an
existing Kiwix installation. Keep ``kiwix_install: True`` when using the IIAB
Admin Console, which requires the Kiwix role to be installed. The Kiwix
Android APK setting is separate.
