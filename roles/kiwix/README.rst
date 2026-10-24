============
Kiwix README
============

Kiwix develops ZIM file creation & rendering tools for offline action,
as summarized at: https://wiki.kiwix.org/wiki/Software

Internet-in-a-Box uses `kiwix-tools <https://github.com/kiwix/kiwix-tools>`_ executables like kiwix-serve (in
``/opt/iiab/kiwix/bin``) to render ZIM files (such as Wikipedia, and
other educational materials) typically from https://download.kiwix.org/zim/

IIAB's catalog builder (``iiab-make-kiwix-lib.py``) scans ZIM metadata with
``python3-libzim`` directly; ``kiwix-manage`` remains available for debugging
but is no longer called by IIAB.

Locations
---------

- Your ZIM files go in ``/library/zims/content``
- Your ZIM index files used to go in directories under ``/library/zims/index`` (these index files are increasingly no longer necessary, as most ZIM files produced since 2017 contain an internal search index instead!)
- The URL is http://box/kiwix or http://box.lan/kiwix (both proxied for AWStats, Matomo, ETC)
- Use URL http://box:3000/kiwix if you want to avoid the proxy

Your ``/library/zims/library.opds`` (containing essential metadata for the ZIM
files you've installed) can be regenerated if necessary, by running:
``/usr/bin/iiab-make-kiwix-lib``

The ZIM files in ``/library/zims/content`` are the source of truth. Metadata is
cached in ``/library/zims/catalog.sqlite``; only new or resized ZIMs are
reopened, invalid ZIMs are skipped with a warning, and the library file is
written atomically. ``iiab-make-kiwix-lib.py`` writes OPDS when the installed
libkiwix supports it (14.3+) and classic XML otherwise.

See also "How do I add ZIM files, like Wikipedia?" at http://FAQ.IIAB.IO
