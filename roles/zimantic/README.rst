=============
Zimantic
=============

Zimantic provides meaning-based, title-word, and native ZIM full-text search,
plus direct article serving from local ZIM archives.

This role is opt-in. It does not replace ``kiwix-serve`` by default because
Zimantic currently needs Python 3.11-3.14, compatible 64-bit Linux native
wheels, and more disk space for its Python environment. ``libzim`` publishes
wheels for specific Python versions, so choose ``zimantic_python`` only after
confirming that the selected interpreter has a compatible wheel. Existing
IIAB Kiwix URLs and the Kiwix Android APK remain unchanged by default.

Configuration
-------------

Set these variables in ``/etc/iiab/local_vars.yml`` and run the role::

    zimantic_install: True
    zimantic_enabled: True
    zimantic_mode: fast

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

The default ``fast`` mode uses about 66 MiB RSS with one small ZIM and needs no
model. It uses ZIM-native full-text search and title-word search when a fast
index has been built. Zimantic opens every archive below ``zimantic_zim_dir``;
RSS therefore grows with the number and size of ZIMs. A test with 761 archives
used about 646 MiB RSS, so a Pi Zero 2 W should use a small selected ZIM
directory rather than the complete IIAB library. The server is available at
``http://box/zimantic`` through NGINX. The service also listens on
``http://box:8090/`` for troubleshooting and direct access.

Semantic mode requires a 64-bit ``aarch64`` or ``x86_64`` host with a
compatible Python version. The role downloads the approximately 123 MiB
embedding model when it is missing::

    zimantic_mode: semantic

The semantic server benchmark is approximately 323 MiB RSS. A full semantic
index build is intentionally not run by this role because it can be expensive
on small devices. Build indexes during a maintenance window with::

    cd /library/zimantic && sudo -u zimantic /opt/iiab/zimantic/.venv/bin/zimantic build --fast

For semantic indexes, build on a faster compatible machine and copy the
resulting files into ``/library/zimantic/indexes`` before reloading the
service. Set ``zimantic_zim_dir`` to a directory containing only the archives
you want Zimantic to search when memory is constrained; the default points at
IIAB's complete ``/library/zims/content`` directory.

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
