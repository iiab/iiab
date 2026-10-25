#!/usr/bin/python3
'''
IIAB ZIM catalog.

The ZIM directory is the source of truth.  This module scans it, caches the
metadata of every readable ZIM in a single SQLite database, and exports a
library file for kiwix-serve.

The SQLite database is a disposable cache, not a system of record:

  * it is rebuilt from the ZIM files whenever it is missing or has an
    incompatible schema version;
  * a ZIM whose size and mtime have not changed since the last scan is not
    reopened;
  * an unreadable (invalid, truncated, permission-denied) ZIM is skipped,
    logged and left out of the catalog;
  * a missing content directory (unmounted drive, broken symlink) is an
    error, so the previous cache and library are kept;
  * rows for ZIM files that disappeared are removed.

The exported library file is also derived.  libkiwix 14 reads classic XML;
libkiwix 15 reads OPDS.  This is a clean format break with no migration path.
detect_library_format() picks the format supported by the installed
kiwix-serve.
'''

import argparse
import base64
import datetime
import json
import logging
import os
import re
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from xml.sax import saxutils

# Bump when the cache layout or the metadata derivation changes.  The cache is
# disposable, so a mismatch simply triggers a full rescan.
# Version 4 matches Zimantic's catalog.py column layout.  The two tools still
# store ``path`` differently (relative here, absolute there) and handle
# unreadable ZIMs differently, so do not point them at one shared file yet.
SCHEMA_VERSION = 4
CATALOG_FILENAME = 'catalog.sqlite'
LIBRARY_FILENAME = 'library.opds'
MAX_FAVICON_BYTES = 1 << 20    # ignore pathological illustrations (> 1 MiB)

# Serializes schema creation between threads in one process.  Cross-process
# callers are serialized by BEGIN IMMEDIATE in ZimCatalog._ensure_schema().
_SCHEMA_LOCK = threading.Lock()

# Columns of the zims table, in Zimantic's order.  Checked before trusting
# ``user_version`` so a database written by another tool that reuses the
# filename is rebuilt instead of failing every query.
# ``icon_path`` is populated by Zimantic's HTML icon discovery; IIAB writes ''
# and relies on the embedded illustration.  ``available``/``last_error`` are
# currently always 1/'' here because IIAB removes unreadable rows from the cache
# instead of retaining them; keep both tools' lifecycle rules in sync before
# sharing a catalog file.
_SCHEMA_COLUMNS = (
    'path', 'stem', 'uuid', 'size', 'mtime', 'title', 'description',
    'long_description', 'language', 'creator', 'publisher', 'date', 'tags',
    'public_tags', 'name', 'flavour', 'category', 'article_count',
    'media_count', 'entry_count', 'license', 'scraper', 'source',
    'attribution', 'relation', 'counter', 'homepage', 'has_fulltext_index',
    'favicon', 'favicon_mime', 'icon_path', 'has_illustration', 'available',
    'last_error', 'scanned_at',
)

# ZIM metadata keys copied into the catalog.  Illustration_* keys are handled
# separately, through get_illustration_item().
META_KEYS = ('Title', 'Description', 'LongDescription', 'Language', 'Creator',
             'Publisher', 'Date', 'Tags', 'Name', 'Flavour', 'License',
             'Scraper', 'Source', 'Attribution', 'Relation', 'Counter')

log = logging.getLogger(__name__)


def _text(value):
    '''Return a metadata value as stripped text.'''
    if isinstance(value, bytes):
        value = value.decode('utf-8', 'replace')
    return str(value).strip()


def _maybe(value):
    '''Call value() when a libzim property is exposed as a method.'''
    return value() if callable(value) else value


def _norm_date(value):
    '''Keep YYYY-MM-DD from a ZIM Date metadata value.'''
    value = _text(value)
    match = re.match(r'^(\d{4}-\d{2}-\d{2})', value)
    return match.group(1) if match else ''


def normalize_counter(value):
    '''Sort a ZIM Counter (mime=count;...) from highest to lowest count.'''
    entries = []
    invalid = []
    for entry in _text(value).split(';'):
        entry = entry.strip()
        if not entry:
            continue
        mime, sep, count = entry.partition('=')
        mime = mime.strip()
        count = count.strip()
        if sep and mime and count.isdigit():
            entries.append((mime, int(count)))
        else:
            invalid.append(entry)
    entries.sort(key=lambda item: (-item[1], item[0]))
    return ';'.join(
        ['%s=%d' % (mime, count) for mime, count in entries] + invalid)


def normalize_creator(value):
    '''Treat placeholder creator metadata as missing (same as Zimantic).'''
    value = _text(value)
    return '' if value == '-' else value


def resolve_homepage(archive):
    '''Return the resolved main-entry path (following ``mainPage`` redirects).'''
    try:
        if not _maybe(getattr(archive, 'has_main_entry', False)):
            return ''
        entry = archive.main_entry
        seen = set()
        for _ in range(32):
            if not entry.is_redirect:
                return entry.path or ''
            if entry.path in seen:
                return ''
            seen.add(entry.path)
            entry = entry.get_redirect_entry()
    except Exception:
        return ''
    return ''


def parse_tags(tags):
    '''Turn a Kiwix tags string into a dict (value is '' for bare tags).'''
    result = {}
    for tag in _text(tags).split(';'):
        tag = tag.strip()
        if not tag:
            continue
        key, sep, value = tag.partition(':')
        result[key] = value if sep else ''
    return result


def normalize_tags(tags):
    '''Normalize tags exactly like libkiwix's convertTags().

    Legacy bare tags (nopic/novid/nodet) become _pictures:no etc., and the
    missing defaults (_ftindex:no; _pictures:yes; _videos:yes; _details:yes)
    are appended.  This keeps the catalog identical to what kiwix-manage wrote.
    '''
    parts = [tag.strip() for tag in _text(tags).split(';') if tag.strip()]
    result = []
    pic_seen = vid_seen = det_seen = index_seen = False
    for tag in parts:
        pic_seen = pic_seen or tag == 'nopic' or tag.startswith('_pictures:')
        vid_seen = vid_seen or tag == 'novid' or tag.startswith('_videos:')
        det_seen = det_seen or tag == 'nodet' or tag.startswith('_details:')
        index_seen = index_seen or tag.startswith('_ftindex')
        if tag == 'nopic':
            result.append('_pictures:no')
        elif tag == 'novid':
            result.append('_videos:no')
        elif tag == 'nodet':
            result.append('_details:no')
        elif tag == '_ftindex':
            result.append('_ftindex:yes')
        else:
            result.append(tag)
    if not index_seen:
        result.append('_ftindex:no')
    if not pic_seen:
        result.append('_pictures:yes')
    if not vid_seen:
        result.append('_videos:yes')
    if not det_seen:
        result.append('_details:yes')
    return ';'.join(result)


def category_from_tags(tags):
    '''Return the _category:<value> tag, if any.'''
    return parse_tags(tags).get('_category', '')


def public_tags(tags):
    '''Tags suitable for display (private ``_`` tags removed).'''
    return ';'.join(
        tag for tag in _text(tags).split(';')
        if tag and not tag.startswith('_'))


def perma_ref(stem):
    '''Strip a trailing _YYYY-MM version from a ZIM filename stem.'''
    match = re.search(r'_20[0-9]{2}-(0[1-9]|1[0-2])$', stem)
    return stem[:match.start()] if match else stem


def header_uuid(zim_path):
    '''Read the 16-byte ZIM UUID from the archive header.

    This is the same value as Archive.uuid, but works even if a libzim build
    does not expose that property.
    '''
    with open(zim_path, 'rb') as fp:
        header = fp.read(24)
    if len(header) < 24 or header[:4] != b'ZIM\x04':
        raise ValueError('not a ZIM file')
    return str(uuid.UUID(bytes=header[8:24]))


def _archive_uuid(archive, zim_path):
    try:
        return str(archive.uuid)
    except Exception:
        return header_uuid(zim_path)


def read_zim_metadata(abs_path, rel_path):
    '''Read one ZIM's metadata.  Raises if the ZIM cannot be opened.'''
    # Imported lazily, so read_catalog() works on hosts without libzim.
    from libzim.reader import Archive

    stat = os.stat(abs_path)
    archive = Archive(abs_path)

    try:
        available = {
            key.decode('utf-8', 'replace') if isinstance(key, bytes) else str(key)
            for key in archive.metadata_keys
        }
    except Exception:
        available = set()

    metadata = {}
    for key in META_KEYS:
        if available and key not in available:
            continue
        try:
            metadata[key] = _text(archive.get_metadata(key))
        except Exception:
            continue

    tags = normalize_tags(metadata.get('Tags', ''))
    stem = os.path.basename(rel_path)
    if stem.lower().endswith('.zim'):
        stem = stem[:-4]

    try:
        article_count = getattr(archive, 'article_count', 0)
        if callable(article_count):
            article_count = article_count()
        article_count = int(article_count or 0)
    except Exception:
        article_count = 0
    try:
        media_count = getattr(archive, 'media_count', 0)
        if callable(media_count):
            media_count = media_count()
        media_count = int(media_count or 0)
    except Exception:
        media_count = 0
    try:
        entry_count = int(_maybe(getattr(archive, 'entry_count', 0)) or 0)
    except Exception:
        entry_count = 0
    try:
        has_fulltext_index = 1 if _maybe(
            getattr(archive, 'has_fulltext_index', False)) else 0
    except Exception:
        has_fulltext_index = 0
    homepage = resolve_homepage(archive)

    favicon = b''
    favicon_mime = ''
    try:
        # Size 48 is the catalog thumbnail (libzim's default).  libzim also
        # falls back to the legacy favicon entry for ZIMs without one.
        item = archive.get_illustration_item(48)
        favicon = bytes(item.content)
        favicon_mime = item.mimetype or ''
        if len(favicon) > MAX_FAVICON_BYTES:
            log.warning('ignoring %s illustration of %d bytes (limit %d)',
                        rel_path, len(favicon), MAX_FAVICON_BYTES)
            favicon = b''
            favicon_mime = ''
    except Exception:
        pass

    name = metadata.get('Name', '') or perma_ref(stem)
    creator = normalize_creator(metadata.get('Creator', ''))

    return {
        'path': rel_path,
        'stem': stem,
        'uuid': _archive_uuid(archive, abs_path),
        'size': stat.st_size,
        'mtime': stat.st_mtime,
        'title': metadata.get('Title', ''),
        'description': metadata.get('Description', ''),
        'long_description': metadata.get('LongDescription', ''),
        'language': metadata.get('Language', ''),
        'creator': creator,
        'publisher': metadata.get('Publisher', ''),
        'date': _norm_date(metadata.get('Date', '')),
        'tags': tags,
        'public_tags': public_tags(tags),
        'name': name,
        'flavour': metadata.get('Flavour', ''),
        'category': category_from_tags(tags),
        'article_count': article_count,
        'media_count': media_count,
        'entry_count': entry_count,
        'license': metadata.get('License', ''),
        'scraper': metadata.get('Scraper', ''),
        'source': metadata.get('Source', ''),
        'attribution': metadata.get('Attribution', ''),
        'relation': metadata.get('Relation', ''),
        'counter': normalize_counter(metadata.get('Counter', '')),
        'homepage': homepage,
        'has_fulltext_index': has_fulltext_index,
        'favicon': favicon,
        'favicon_mime': favicon_mime,
        # HTML-discovered icons are a Zimantic feature; IIAB relies on the
        # embedded illustration above.
        'icon_path': '',
        'has_illustration': 1 if favicon else 0,
        # IIAB currently drops unreadable ZIMs from the cache instead of
        # keeping them as unavailable; the columns exist for schema parity.
        'available': 1,
        'last_error': '',
        'scanned_at': time.time(),
    }


def metadata_to_book_attrs(meta, exclude_favicon=True):
    '''Convert a metadata record to the classic book-attribute dict.

    Keys and units match what read_library_xml() returned for library.xml:
    size is KiB; articleCount, mediaCount and size are strings; favicon is
    base64.
    '''
    attrs = {
        # ``id`` remains the legacy dict/OPDS/JSON key.  It is the ZIM UUID,
        # the same value Zimantic calls ``uuid``.
        'id': meta.get('uuid') or meta.get('path', ''),
        'uuid': meta.get('uuid') or '',
        'path': meta.get('path', ''),
        'title': meta.get('title', ''),
        'description': meta.get('description', ''),
        'language': meta.get('language', ''),
        'creator': meta.get('creator', ''),
        'publisher': meta.get('publisher', ''),
        'name': meta.get('name', ''),
        'flavour': meta.get('flavour', ''),
        'category': meta.get('category', ''),
        'tags': meta.get('tags', ''),
        'date': meta.get('date', ''),
        'articleCount': str(meta.get('article_count', 0)),
        'mediaCount': str(meta.get('media_count', 0)),
        'size': str(int(meta.get('size', 0)) >> 10),    # KiB, as in library.xml
    }
    if meta.get('license'):
        attrs['license'] = meta['license']
    if meta.get('scraper'):
        attrs['scraper'] = meta['scraper']
    for key in ('source', 'attribution', 'relation', 'counter', 'homepage'):
        if meta.get(key):
            attrs[key] = meta[key]
    if meta.get('favicon_mime'):
        attrs['faviconMimeType'] = meta['favicon_mime']
    if not exclude_favicon and meta.get('favicon'):
        attrs['favicon'] = base64.b64encode(meta['favicon']).decode('ascii')
    return {key: value for key, value in attrs.items() if value != ''}


def detect_library_format(kiwix_serve_path):
    '''Return 'opds' or 'xml' for the installed kiwix-serve.

    libkiwix 15 reads OPDS; older versions read classic XML only.  If the
    version cannot be determined, fall back to XML, which libkiwix 14
    understands.
    '''
    try:
        output = subprocess.check_output(
            [kiwix_serve_path, '--version'],
            stderr=subprocess.STDOUT, text=True, timeout=10)
    except Exception as error:
        log.warning('cannot determine kiwix-serve version (%s); using XML', error)
        return 'xml'

    match = re.search(r'libkiwix\s+(\d+)\.(\d+)', output)
    if not match:
        log.warning('cannot parse kiwix-serve version from %r; using XML', output)
        return 'xml'
    version = (int(match.group(1)), int(match.group(2)))
    return 'opds' if version >= (15, 0) else 'xml'


class ZimCatalog:
    '''SQLite metadata cache for the ZIM files under one zim_path.'''

    def __init__(self, db_path, zim_path=None, verbose=False):
        self.db_path = db_path
        self.zim_path = os.path.abspath(zim_path) if zim_path else None
        self.content_dir = (os.path.join(self.zim_path, 'content')
                            if self.zim_path else None)
        self.verbose = verbose
        self.db: sqlite3.Connection | None = self._connect()
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        if self.db_path != ':memory:':
            parent = os.path.dirname(os.path.abspath(self.db_path))
            if parent:
                os.makedirs(parent, exist_ok=True)
        db = sqlite3.connect(self.db_path, timeout=30)
        db.row_factory = sqlite3.Row
        if self.db_path != ':memory:':
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('PRAGMA synchronous=NORMAL')
        db.execute('PRAGMA busy_timeout=30000')
        return db

    def _connection(self) -> sqlite3.Connection:
        if self.db is None:
            raise RuntimeError('catalog is closed')
        return self.db

    def _ensure_schema(self):
        # The version alone is not enough: another tool may have written this
        # file with a different layout (Zimantic's catalog.py uses the same
        # filename and a different schema), so verify the columns too.
        with _SCHEMA_LOCK:
            db = self._connection()
            db.execute('BEGIN IMMEDIATE')
            try:
                version = db.execute('PRAGMA user_version').fetchone()[0]
                columns = {
                    row['name']
                    for row in db.execute('PRAGMA table_info(zims)')
                }
                current = (version == SCHEMA_VERSION
                           and columns == set(_SCHEMA_COLUMNS))
                if not current and version != 0:
                    reason = ('schema version %s' % version
                              if version != SCHEMA_VERSION
                              else 'a different table layout')
                    log.warning('%s has %s, rebuilding (wanted version %s)',
                                self.db_path, reason, SCHEMA_VERSION)
                if not current:
                    db.execute('DROP TABLE IF EXISTS zims')
                    db.execute('''
                        CREATE TABLE zims (
                            path TEXT PRIMARY KEY,
                            stem TEXT NOT NULL,
                            uuid TEXT NOT NULL DEFAULT '',
                            size INTEGER NOT NULL,
                            mtime REAL NOT NULL,
                            title TEXT NOT NULL DEFAULT '',
                            description TEXT NOT NULL DEFAULT '',
                            long_description TEXT NOT NULL DEFAULT '',
                            language TEXT NOT NULL DEFAULT '',
                            creator TEXT NOT NULL DEFAULT '',
                            publisher TEXT NOT NULL DEFAULT '',
                            date TEXT NOT NULL DEFAULT '',
                            tags TEXT NOT NULL DEFAULT '',
                            public_tags TEXT NOT NULL DEFAULT '',
                            name TEXT NOT NULL DEFAULT '',
                            flavour TEXT NOT NULL DEFAULT '',
                            category TEXT NOT NULL DEFAULT '',
                            article_count INTEGER NOT NULL DEFAULT 0,
                            media_count INTEGER NOT NULL DEFAULT 0,
                            entry_count INTEGER NOT NULL DEFAULT 0,
                            license TEXT NOT NULL DEFAULT '',
                            scraper TEXT NOT NULL DEFAULT '',
                            source TEXT NOT NULL DEFAULT '',
                            attribution TEXT NOT NULL DEFAULT '',
                            relation TEXT NOT NULL DEFAULT '',
                            counter TEXT NOT NULL DEFAULT '',
                            homepage TEXT NOT NULL DEFAULT '',
                            has_fulltext_index INTEGER NOT NULL DEFAULT 0,
                            favicon BLOB,
                            favicon_mime TEXT NOT NULL DEFAULT '',
                            icon_path TEXT NOT NULL DEFAULT '',
                            has_illustration INTEGER NOT NULL DEFAULT 0,
                            available INTEGER NOT NULL DEFAULT 1,
                            last_error TEXT NOT NULL DEFAULT '',
                            scanned_at REAL NOT NULL
                        )
                    ''')
                    db.execute('CREATE INDEX zims_stem ON zims(stem)')
                    db.execute('CREATE INDEX zims_uuid ON zims(uuid)')
                    db.execute('PRAGMA user_version = %d' % SCHEMA_VERSION)
                db.commit()
            except BaseException:
                db.rollback()
                raise

    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None

    def _existing(self):
        return {row['path']: (row['size'], row['mtime'])
                for row in self._connection().execute(
                    'SELECT path, size, mtime FROM zims')}

    def _zim_files(self):
        '''Return {relative path: (size, mtime)} for every .zim under content/.'''
        if not self.content_dir or not os.path.isdir(self.content_dir):
            # Do not treat an absent content directory (unmounted drive,
            # broken symlink, typo) as "every ZIM was removed": scan() would
            # then delete the cache and publish an empty library.
            raise FileNotFoundError(
                'ZIM content directory does not exist: %s' % self.content_dir)
        files = {}
        for root, dirs, names in os.walk(self.content_dir):
            dirs[:] = [name for name in dirs if not name.startswith('.')]
            for name in names:
                if not name.lower().endswith('.zim'):
                    continue
                abs_path = os.path.join(root, name)
                try:
                    stat = os.stat(abs_path)
                except OSError as error:
                    log.warning('cannot stat %s: %s', abs_path, error)
                    continue
                rel_path = os.path.relpath(abs_path, self.zim_path)
                files[rel_path.replace(os.sep, '/')] = (stat.st_size,
                                                        stat.st_mtime)
        return files

    def scan(self, force=False):
        '''Reconcile the cache with the ZIM directory.

        Returns a dict with added/updated/removed/skipped/invalid counts.
        '''
        if not self.zim_path:
            raise ValueError('scan() needs a zim_path')

        files = self._zim_files()
        existing = self._existing()
        stats = {'added': 0, 'updated': 0, 'removed': 0,
                 'skipped': 0, 'invalid': 0, 'total': len(files)}
        stale = set(existing) - set(files)

        for rel_path in sorted(files):
            size, mtime = files[rel_path]
            recorded = existing.get(rel_path)
            if (not force
                    and recorded is not None
                    and recorded[0] == size
                    and abs(recorded[1] - mtime) < 1e-6):
                stats['skipped'] += 1
                continue
            abs_path = os.path.join(self.zim_path, rel_path)
            try:
                meta = read_zim_metadata(abs_path, rel_path)
            except Exception as error:
                # Invalid/truncated/unreadable: leave it out of the catalog and
                # retry on the next run (the user can repair or replace it).
                log.warning('skipping invalid ZIM %s: %s', rel_path, error)
                stale.add(rel_path)
                stats['invalid'] += 1
                continue

            if rel_path in existing:
                stats['updated'] += 1
            else:
                stats['added'] += 1
            self._upsert(meta)

        for rel_path in stale:
            if rel_path in existing:
                self._connection().execute(
                    'DELETE FROM zims WHERE path = ?', (rel_path,))
                stats['removed'] += 1

        self._connection().commit()
        log.info('catalog: %s', stats)
        return stats

    def _upsert(self, meta):
        self._connection().execute('''
            INSERT INTO zims (
                path, stem, uuid, size, mtime, title, description,
                long_description, language, creator, publisher, date, tags,
                public_tags, name, flavour, category, article_count,
                media_count, entry_count, license, scraper, source,
                attribution, relation, counter, homepage, has_fulltext_index,
                favicon, favicon_mime, icon_path, has_illustration, available,
                last_error, scanned_at
            ) VALUES (
                :path, :stem, :uuid, :size, :mtime, :title, :description,
                :long_description, :language, :creator, :publisher, :date,
                :tags, :public_tags, :name, :flavour, :category,
                :article_count, :media_count, :entry_count, :license,
                :scraper, :source, :attribution, :relation, :counter,
                :homepage, :has_fulltext_index, :favicon, :favicon_mime,
                :icon_path, :has_illustration, :available, :last_error,
                :scanned_at
            )
            ON CONFLICT(path) DO UPDATE SET
                stem=excluded.stem, uuid=excluded.uuid,
                size=excluded.size, mtime=excluded.mtime,
                title=excluded.title, description=excluded.description,
                long_description=excluded.long_description,
                language=excluded.language, creator=excluded.creator,
                publisher=excluded.publisher, date=excluded.date,
                tags=excluded.tags, public_tags=excluded.public_tags,
                name=excluded.name,
                flavour=excluded.flavour, category=excluded.category,
                article_count=excluded.article_count,
                media_count=excluded.media_count,
                entry_count=excluded.entry_count, license=excluded.license,
                scraper=excluded.scraper, source=excluded.source,
                attribution=excluded.attribution, relation=excluded.relation,
                counter=excluded.counter, homepage=excluded.homepage,
                has_fulltext_index=excluded.has_fulltext_index,
                favicon=excluded.favicon,
                favicon_mime=excluded.favicon_mime,
                icon_path=excluded.icon_path,
                has_illustration=excluded.has_illustration,
                available=excluded.available,
                last_error=excluded.last_error,
                scanned_at=excluded.scanned_at
        ''', {
            **meta,
            'favicon': sqlite3.Binary(meta['favicon']) if meta.get('favicon') else None,
        })

    def rows(self):
        return self._connection().execute(
            'SELECT * FROM zims ORDER BY path').fetchall()

    def unique_rows(self):
        '''Return one deterministic row per ZIM UUID.

        The UUID is the book identity; the path is only the file identity.  A
        ZIM copied under another filename has the same UUID, so keep the copy
        with the shortest path.  Used by every consumer that publishes books, so
        the library file and the Admin Console menu agree.
        '''
        chosen = {}
        for row in self.rows():
            record = dict(row)
            key = record.get('uuid') or record.get('path')
            current = chosen.get(key)
            if current is None:
                chosen[key] = record
                continue
            new_path = record.get('path', '')
            old_path = current.get('path', '')
            if (len(new_path), new_path) < (len(old_path), old_path):
                log.warning('duplicate ZIM UUID %s: using %s instead of %s',
                            key, new_path, old_path)
                chosen[key] = record
            else:
                log.warning('duplicate ZIM UUID %s: ignoring %s',
                            key, new_path)
        return sorted(chosen.values(), key=lambda record: record.get('path', ''))

    def book_dict(self, exclude_favicon=True):
        '''Return (zims keyed by UUID, map of relative path -> UUID).'''
        zims = {}
        path_to_id = {}
        for record in self.unique_rows():
            attrs = metadata_to_book_attrs(record, exclude_favicon)
            zim_id = attrs.get('uuid') or attrs.get('id') or attrs.get('path')
            if not zim_id:
                continue
            zims[zim_id] = attrs
            path_to_id[attrs['path']] = zim_id
        return zims, path_to_id

    def write_opds(self, library_path, include_favicon=True):
        '''Write a libkiwix-compatible OPDS feed atomically.'''
        if not self.zim_path:
            raise ValueError('write_opds() needs a zim_path')
        library_path = os.path.abspath(library_path)
        lib_dir = os.path.dirname(library_path)
        now = datetime.datetime.now(datetime.timezone.utc).strftime(
            '%Y-%m-%dT%H:%M:%SZ')
        feed_id = 'urn:uuid:' + str(uuid.uuid5(uuid.NAMESPACE_URL,
                                               self.zim_path))

        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>\n',
            '<feed xmlns="http://www.w3.org/2005/Atom" '
            'xmlns:dc="http://purl.org/dc/terms/">\n',
            '  <id>%s</id>\n' % saxutils.escape(feed_id),
            '  <title>Internet in a Box</title>\n',
            '  <updated>%s</updated>\n' % now,
        ]

        count = 0
        for meta in self.unique_rows():
            attrs = metadata_to_book_attrs(meta, exclude_favicon=True)
            href = os.path.relpath(os.path.join(self.zim_path, attrs['path']),
                                   lib_dir).replace(os.sep, '/')
            date = attrs.get('date', '')
            updated = (date + 'T00:00:00Z') if date else now
            parts.append('  <entry>\n')
            parts.append('    <id>urn:uuid:%s</id>\n'
                         % saxutils.escape(attrs.get('id', '')))
            parts.append('    <title>%s</title>\n'
                         % saxutils.escape(attrs.get('title', '')))
            parts.append('    <updated>%s</updated>\n' % updated)
            parts.append('    <summary>%s</summary>\n'
                         % saxutils.escape(attrs.get('description', '')))
            for tag in ('language', 'name', 'flavour', 'category', 'tags'):
                parts.append('    <%s>%s</%s>\n'
                             % (tag, saxutils.escape(attrs.get(tag, '')), tag))
            parts.append('    <articleCount>%s</articleCount>\n'
                         % attrs.get('articleCount', '0'))
            parts.append('    <mediaCount>%s</mediaCount>\n'
                         % attrs.get('mediaCount', '0'))
            parts.append('    <author><name>%s</name></author>\n'
                         % saxutils.escape(attrs.get('creator', '')))
            parts.append('    <publisher><name>%s</name></publisher>\n'
                         % saxutils.escape(attrs.get('publisher', '')))
            if date:
                # dc:issued is the publication date; omit it for undated ZIMs
                # (atom:updated above already carries the feed-generation time).
                parts.append('    <dc:issued>%s</dc:issued>\n' % updated)
            if include_favicon and meta.get('favicon'):
                mime = meta.get('favicon_mime') or 'image/png'
                encoded = base64.b64encode(meta['favicon']).decode('ascii')
                parts.append(
                    '    <link rel="http://opds-spec.org/image/thumbnail" '
                    'type=%s href=%s/>\n'
                    % (saxutils.quoteattr(mime),
                       saxutils.quoteattr('data:%s;base64,%s' % (mime, encoded))))
            parts.append(
                '    <link rel="http://opds-spec.org/acquisition/open-access" '
                'type="application/x-zim" href=%s length="%s"/>\n'
                % (saxutils.quoteattr(href), meta['size']))
            parts.append('  </entry>\n')
            count += 1

        parts.append('</feed>\n')
        self._atomic_write(library_path, ''.join(parts))
        return count

    def write_xml(self, library_path):
        '''Write the classic library.xml format (for libkiwix < 15).'''
        if not self.zim_path:
            raise ValueError('write_xml() needs a zim_path')
        library_path = os.path.abspath(library_path)
        lib_dir = os.path.dirname(library_path)
        parts = ['<?xml version="1.0" encoding="UTF-8"?>\n',
                 '<library version="20110515">\n']
        count = 0
        for meta in self.unique_rows():
            attrs = metadata_to_book_attrs(meta, exclude_favicon=False)
            href = os.path.relpath(os.path.join(self.zim_path, attrs['path']),
                                   lib_dir).replace(os.sep, '/')
            attrs['path'] = href
            order = ('id', 'path', 'title', 'description', 'language',
                     'creator', 'publisher', 'name', 'flavour', 'category',
                     'tags', 'articleCount', 'mediaCount', 'date', 'size',
                     'faviconMimeType', 'favicon')
            rendered = ' '.join(
                '%s=%s' % (key, saxutils.quoteattr(str(attrs[key])))
                for key in order if attrs.get(key, '') != '')
            parts.append('  <book %s/>\n' % rendered)
            count += 1
        parts.append('</library>\n')
        self._atomic_write(library_path, ''.join(parts))
        return count

    @staticmethod
    def _atomic_write(path, content):
        tmp_path = path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as fp:
            fp.write(content)
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(tmp_path, path)


def read_catalog(db_path, kiwix_exclude_attr=('favicon',)):
    '''Read a catalog cache and return the classic (zims, path_to_id) tuple.'''
    if not db_path or not os.path.exists(db_path):
        return {}, {}
    catalog = ZimCatalog(db_path)
    try:
        return catalog.book_dict('favicon' in kiwix_exclude_attr)
    finally:
        catalog.close()


def _default_paths():
    try:
        import iiab.iiab_const as const
    except Exception:
        return None, None, None
    zim_path = getattr(const, 'zim_path', None)
    catalog_db = getattr(const, 'zim_catalog_db',
                         os.path.join(zim_path, CATALOG_FILENAME)
                         if zim_path else None)
    library_path = getattr(const, 'kiwix_library_path',
                           os.path.join(zim_path, LIBRARY_FILENAME)
                           if zim_path else None)
    return zim_path, catalog_db, library_path


def main(argv=None):
    zim_path_default, catalog_default, library_default = _default_paths()
    parser = argparse.ArgumentParser(
        description='Scan ZIM files into the IIAB catalog cache and export a '
                    'kiwix-serve library file.')
    parser.add_argument('--zim-path', default=zim_path_default,
                        help='root containing content/*.zim '
                             '(default: iiab_const.zim_path)')
    parser.add_argument('--catalog', default=catalog_default,
                        help='SQLite cache path '
                             '(default: iiab_const.zim_catalog_db)')
    parser.add_argument('--library', default=library_default,
                        help='library file to write '
                             '(default: iiab_const.kiwix_library_path)')
    parser.add_argument('--format', choices=('auto', 'opds', 'xml'),
                        default='auto',
                        help='library format; auto uses the installed libkiwix version')
    parser.add_argument('--kiwix-serve', default=None,
                        help='kiwix-serve path for --format auto')
    parser.add_argument('--force', action='store_true',
                        help='reopen every ZIM, even if its size and mtime '
                             'are unchanged')
    parser.add_argument('--json', action='store_true',
                        help='print the book dict as JSON; do not write a library')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format='%(levelname)s: %(message)s')

    if not args.zim_path:
        parser.error('--zim-path is required (or set iiab_const.zim_path)')
    zim_path = args.zim_path
    catalog_path = args.catalog or os.path.join(zim_path, CATALOG_FILENAME)
    library_path = args.library or os.path.join(zim_path, LIBRARY_FILENAME)

    catalog = ZimCatalog(catalog_path, zim_path, verbose=args.verbose)
    try:
        try:
            stats = catalog.scan(force=args.force)
        except FileNotFoundError as error:
            print('ERROR: %s' % error, file=sys.stderr)
            return 1
        if args.json:
            zims, _ = catalog.book_dict()
            try:
                json.dump(zims, sys.stdout)
                sys.stdout.write('\n')
            except BrokenPipeError:
                pass
            return 0

        fmt = args.format
        if fmt == 'auto':
            kiwix_serve = args.kiwix_serve
            if not kiwix_serve:
                try:
                    import iiab.iiab_const as const
                    kiwix_serve = getattr(
                        const, 'kiwix_serve',
                        os.path.join(const.iiab_base_path,
                                     'kiwix', 'bin', 'kiwix-serve'))
                except Exception:
                    kiwix_serve = 'kiwix-serve'
            fmt = detect_library_format(kiwix_serve)
        count = (catalog.write_opds(library_path) if fmt == 'opds'
                 else catalog.write_xml(library_path))
        logging.getLogger(__name__).info(
            'wrote %s (%s, %d books) from %s', library_path, fmt, count,
            catalog_path)
        if args.verbose:
            sys.stderr.write('catalog stats: %s\n' % stats)
        return 0
    finally:
        catalog.close()


if __name__ == '__main__':
    sys.exit(main())
