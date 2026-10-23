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

The role checks out ``zimantic_version`` on every run and reinstalls the
Python package when the checkout changes. After pulling a newer IIAB revision,
run::

    cd /opt/iiab/iiab
    git pull
    sudo ./runrole zimantic

``sudo ./runrole --reinstall zimantic`` is not needed for upgrades: the role
detects the new checkout itself. It only forces the Python package to be
reinstalled.

The source checkout under ``zimantic_source_dir`` is treated as disposable:
the role discards local tracked changes there when checking out the requested
version. Runtime data, indexes, and models are kept separately under
``zimantic_data_dir`` and are never deleted automatically, including when
``zimantic_mode`` changes. Changing the mode rewrites the configuration and
systemd unit and restarts the service. Switching back to ``semantic`` does not
re-download the model, and a ``fast`` index is upgraded in place when a
semantic build is run.

A full reset is normally unnecessary. If you intentionally want to start over
with the default paths, stop the service and remove the source and runtime
data directories::

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
compatible Python version and the approximately 123 MiB embedding model::

    zimantic_mode: semantic
    zimantic_download_model: True

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
