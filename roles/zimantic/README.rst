=============
Zimantic
=============

Zimantic provides meaning-based, title-word, and native ZIM full-text search,
plus direct article serving from local ZIM archives.

This role is opt-in. It does not replace ``kiwix-serve`` by default because
Zimantic currently requires Python 3.14, 64-bit Linux native wheels, and more
disk space for its Python environment. Existing IIAB Kiwix URLs and the
Kiwix Android APK remain unchanged.

Configuration
-------------

Set these variables in ``/etc/iiab/local_vars.yml`` and run the role::

    zimantic_install: True
    zimantic_enabled: True
    zimantic_mode: fast

The default ``fast`` mode uses about 66 MiB RSS with one small ZIM and needs no
model. It uses ZIM-native full-text search and title-word search when a fast
index has been built. Zimantic opens every archive below ``zimantic_zim_dir``;
RSS therefore grows with the number and size of ZIMs. A test with 761 archives
used about 646 MiB RSS, so a Pi Zero 2 W should use a small selected ZIM
directory rather than the complete IIAB library. The server is available at
``http://box:8090/``; ``http://box/zimantic`` redirects there.

Semantic mode requires a 64-bit ``aarch64`` or ``x86_64`` host with Python
3.14 and the approximately 123 MiB embedding model::

    zimantic_mode: semantic
    zimantic_download_model: True

The semantic server benchmark is approximately 323 MiB RSS. A full semantic
index build is intentionally not run by this role because it can be expensive
on small devices. Build indexes during a maintenance window with::

    sudo -u zimantic /opt/iiab/zimantic/.venv/bin/zimantic build --fast

For semantic indexes, build on a faster compatible machine and copy the
resulting files into ``/library/zimantic/indexes`` before reloading the
service. Set ``zimantic_zim_dir`` to a directory containing only the archives
you want Zimantic to search when memory is constrained; the default points at
IIAB's complete ``/library/zims/content`` directory.

Relationship to Kiwix
---------------------

The role reads ``/library/zims/content`` directly and does not need
``kiwix-serve`` for local results. Kiwix remains useful for its existing
library catalog, compatibility URLs, and Android app. Replacing it entirely
should wait until Python 3.14 is available in IIAB's supported images and
the content URL/search behavior is validated on each target profile.
