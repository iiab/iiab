=============
Zimantic
=============

Zimantic provides meaning-based, title-word, and native ZIM full-text search,
plus direct article serving from local ZIM archives.

This role is opt-in. It does not replace ``kiwix-serve`` by default because
Zimantic currently needs Python 3.11-3.14, compatible native dependencies, and
more disk space for its Python environment. ``libzim`` publishes wheels for
specific Python versions, so choose ``zimantic_python`` only after confirming
that the selected interpreter has a compatible wheel. On 32-bit ``armhf`` hosts,
where no wheels are published, the role installs the native dependencies from
Debian 13/trixie or newer instead. Existing IIAB Kiwix URLs and the Kiwix
Android APK remain unchanged by default.

Configuration
-------------

Set these variables in ``/etc/iiab/local_vars.yml`` and run the role.

Fast mode
~~~~~~~~~

``fast`` is the default and needs no embedding model. Set::

    zimantic_install: True
    zimantic_enabled: True
    zimantic_mode: fast

Fast mode uses about 66 MiB RSS with one small ZIM. It uses ZIM-native
full-text search and title-word search when a fast index has been built.
Zimantic opens every archive below ``zimantic_zim_dir``; RSS therefore grows
with the number and size of ZIMs. A test with 761 archives used about 646 MiB
RSS, so a Pi Zero 2 W should use a small selected ZIM directory rather than the
complete IIAB library. The server is available at ``http://box/zimantic``
through NGINX. The service also listens on ``http://box:8090/`` for
troubleshooting and direct access.

Semantic mode
~~~~~~~~~~~~~

``semantic`` adds meaning-based search. The role downloads the selected
embedding model when it is missing. Set::

    zimantic_install: True
    zimantic_enabled: True
    zimantic_mode: semantic

The semantic server benchmark with ``multilingual-e5-small`` is approximately
323 MiB RSS; ``e5-small-v2`` uses less. 64-bit ``aarch64`` and ``x86_64`` hosts
use the PyPI wheels. 32-bit ``armhf``/``armv7`` hosts have no wheels, so by
default the role installs ``python3-onnxruntime``, ``python3-faiss``,
``python3-libzim``, ``python3-sentencepiece`` and the other native dependencies
as distribution packages, then creates the virtual environment with
``--system-site-packages``. This requires Debian 13/trixie or newer.

Embedding model
~~~~~~~~~~~~~~~

``zimantic_embedding_model`` selects the model:

- ``auto`` (default) uses ``e5-small-v2`` on hosts with 1 GB RAM or less and
  ``multilingual-e5-small`` otherwise.
- ``multilingual-e5-small`` is about 123 MiB and searches 100+ languages.
- ``e5-small-v2`` is about 34 MiB, English only, and saves roughly 125 MiB of
  resident memory.

Indexes are specific to the model that built them, so rebuild every index after
changing ``zimantic_embedding_model`` (``zimantic build --force``).

Native dependencies
~~~~~~~~~~~~~~~~~~~

``zimantic_use_system_packages`` controls where the native dependencies come
from:

- ``auto`` (default) uses PyPI wheels on 64-bit hosts and distribution
  packages on ``armhf``/``armv7``.
- ``always`` uses distribution packages on every architecture and therefore
  requires Debian 13/trixie or newer.
- ``never`` always uses PyPI wheels; this fails on ``armhf``/``armv7`` because
  no wheels are published.

Indexes
~~~~~~~

The role does not build indexes. Build a fast (title and full-text) index
during a maintenance window::

    cd /library/zimantic && sudo -u zimantic /opt/iiab/zimantic/.venv/bin/zimantic build --fast

A full semantic index build is intentionally not run by this role because it
can be expensive on small devices. Build semantic indexes on a faster
compatible machine and copy the resulting files into
``/library/zimantic/indexes`` before reloading the service. Set
``zimantic_zim_dir`` to a directory containing only the archives you want
Zimantic to search when memory is constrained; the default points at IIAB's
complete ``/library/zims/content`` directory.

Upgrading
---------

``./runrole zimantic`` is the normal command. It checks out
``zimantic_version``, reinstalls the Python package when the checkout changes,
re-templates the configuration and systemd unit, and restarts only when
something changed. After pulling a newer IIAB revision, run::

    cd /opt/iiab/iiab
    git pull
    sudo ./runrole zimantic

The other verbs are::

    sudo ./runrole --upgrade zimantic          # force the upgrade/install path
    sudo ./runrole --reinstall zimantic        # reinstall the program
    sudo ./runrole --force-reinstall zimantic  # reset settings, indexes, and model
    sudo ./runrole --status zimantic           # show installed/desired state

``--reinstall`` recreates ``zimantic_venv`` and re-runs the Python package
install, keeping data, indexes, and settings.

``--force-reinstall`` also deletes ``zimantic_source_dir`` and
``zimantic_data_dir`` (indexes, model, ``config.toml``) so the role rebuilds
everything from scratch. In ``semantic`` mode this downloads the model again,
so it needs network access. Both commands require an existing ``zimantic``
entry in ``/etc/iiab/iiab_state.yml`` and ask for ``yes`` unless ``-y`` is
given.

The source directory under ``zimantic_source_dir`` is disposable: the role
discards local tracked changes there when checking out the requested version.
Runtime data, indexes, and models live under ``zimantic_data_dir``. Changing
``zimantic_mode`` rewrites the configuration and systemd unit and restarts the
service. Switching to ``semantic`` downloads the model if it is missing; a
``fast`` index is upgraded in place when a semantic build is run.

The same erase can be done manually, then rerun the role::

    sudo systemctl stop zimantic
    sudo rm -rf /library/zimantic /opt/iiab/zimantic

``zimantic_version`` is a git tag, while pip reports the package version from
Zimantic's ``pyproject.toml``. These values should match without manually
editing the checkout; if pip reports an older version, use a corrected
Zimantic tag or release rather than changing ``pyproject.toml`` on the device.

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
