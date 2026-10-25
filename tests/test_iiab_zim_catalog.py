"""Tests for roles/pylibs/templates/iiab_zim_catalog.py.

Run with:  python3 -m unittest discover -s tests -v

The catalog is an Ansible template, so it is loaded from its path instead of
being imported as a package module.
"""

import base64
import importlib.util
import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from libzim.writer import Creator, Hint, Item, StringProvider

CATALOG_PATH = (
    Path(__file__).resolve().parent.parent
    / "roles"
    / "pylibs"
    / "templates"
    / "iiab_zim_catalog.py"
)
spec = importlib.util.spec_from_file_location("iiab_zim_catalog", CATALOG_PATH)
catalog_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog_module)

ALPHA_HTML = (
    "<html><body><p>Alpha is a sufficiently long article about tires and "
    "wheels that passes the minimum block length for indexing.</p></body></html>"
)


class _Page(Item):
    def __init__(self, path, title, html):
        super().__init__()
        self._path = path
        self._title = title
        self._html = html.encode("utf-8") if isinstance(html, str) else html

    def get_path(self):
        return self._path

    def get_title(self):
        return self._title

    def get_mimetype(self):
        return "text/html"

    def get_contentprovider(self):
        return StringProvider(self._html)

    def get_hints(self):
        return {Hint.FRONT_ARTICLE: True}


def _create_zim(path, *, creator_metadata=None, tags_metadata=None,
                illustration=False):
    creator = Creator(str(path))
    creator.config_indexing(True, "eng")
    creator.set_mainpath("Alpha")
    with creator:
        if creator_metadata is not None:
            creator.add_metadata("Creator", creator_metadata)
        if tags_metadata is not None:
            creator.add_metadata("Tags", tags_metadata)
        if illustration:
            creator.add_illustration(48, _PNG_1PX)
        creator.add_item(_Page("Alpha", "Alpha", ALPHA_HTML))


_PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


# The Zimantic catalog layout (schema version 4).  Kept here as a contract:
# changing the shared columns must be a deliberate, coordinated change.
ZIMANTIC_COLUMNS = (
    "path", "stem", "uuid", "size", "mtime", "title", "description",
    "long_description", "language", "creator", "publisher", "date", "tags",
    "public_tags", "name", "flavour", "category", "article_count",
    "media_count", "entry_count", "license", "scraper", "source",
    "attribution", "relation", "counter", "homepage", "has_fulltext_index",
    "favicon", "favicon_mime", "icon_path", "has_illustration", "available",
    "last_error", "scanned_at",
)


class CatalogTests(unittest.TestCase):
    def _layout(self, tmp):
        root = Path(tmp)
        zims = root / "zims"
        (zims / "content").mkdir(parents=True)
        return root, zims

    def test_detect_library_format_matches_libkiwix_major_break(self):
        for version, expected in (("14.3.0", "xml"), ("15.0.0", "opds")):
            with self.subTest(version=version):
                with patch.object(
                        catalog_module.subprocess, "check_output",
                        return_value="libkiwix %s" % version):
                    self.assertEqual(
                        catalog_module.detect_library_format("kiwix-serve"),
                        expected)

    def test_scan_populates_and_skips_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, zims = self._layout(tmp)
            _create_zim(zims / "content" / "manual.zim")
            catalog = catalog_module.ZimCatalog(
                str(root / "catalog.sqlite"), str(zims))

            first = catalog.scan()
            self.assertEqual(first["added"], 1)
            self.assertEqual(first["total"], 1)
            record = catalog.rows()[0]
            self.assertEqual(record["path"], "content/manual.zim")
            self.assertEqual(record["stem"], "manual")
            self.assertTrue(record["uuid"])
            self.assertIn("_ftindex:no", record["tags"])
            self.assertEqual(record["public_tags"], "")
            self.assertEqual(record["available"], 1)
            self.assertEqual(record["last_error"], "")
            self.assertEqual(record["icon_path"], "")
            self.assertEqual(record["has_illustration"], 0)
            self.assertEqual(catalog.scan()["skipped"], 1)
            catalog.close()

    def test_schema_matches_the_zimantic_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, zims = self._layout(tmp)
            catalog = catalog_module.ZimCatalog(
                str(root / "catalog.sqlite"), str(zims))
            columns = tuple(
                row["name"]
                for row in catalog._connection().execute(
                    "PRAGMA table_info(zims)")
            )
            indexes = {
                row["name"]
                for row in catalog._connection().execute(
                    "PRAGMA index_list(zims)")
                if not row["name"].startswith("sqlite_autoindex_")
            }
            catalog.close()
        self.assertEqual(columns, ZIMANTIC_COLUMNS)
        self.assertEqual(indexes, {"zims_stem", "zims_uuid"})

    def test_placeholder_creator_is_stored_as_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, zims = self._layout(tmp)
            _create_zim(zims / "content" / "manual.zim",
                        creator_metadata="-")
            catalog = catalog_module.ZimCatalog(
                str(root / "catalog.sqlite"), str(zims))
            catalog.scan()
            record = catalog.rows()[0]
            self.assertEqual(record["creator"], "")
            zims_installed, _ = catalog.book_dict()
            self.assertNotIn("creator", next(iter(zims_installed.values())))
            catalog.close()

    def test_public_tags_are_split_from_private_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, zims = self._layout(tmp)
            _create_zim(zims / "content" / "manual.zim",
                        tags_metadata="wikipedia;_ftindex;_category:other")
            catalog = catalog_module.ZimCatalog(
                str(root / "catalog.sqlite"), str(zims))
            catalog.scan()
            record = catalog.rows()[0]
            self.assertIn("_ftindex:yes", record["tags"])
            self.assertEqual(record["public_tags"], "wikipedia")
            self.assertEqual(record["category"], "other")
            catalog.close()

    def test_embedded_illustration_is_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, zims = self._layout(tmp)
            _create_zim(zims / "content" / "manual.zim", illustration=True)
            catalog = catalog_module.ZimCatalog(
                str(root / "catalog.sqlite"), str(zims))
            catalog.scan()
            record = catalog.rows()[0]
            self.assertEqual(record["has_illustration"], 1)
            self.assertEqual(record["favicon_mime"], "image/png")
            self.assertTrue(record["favicon"])
            self.assertEqual(record["icon_path"], "")
            catalog.close()

    def test_missing_content_directory_keeps_the_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, zims = self._layout(tmp)
            _create_zim(zims / "content" / "manual.zim")
            db = str(root / "catalog.sqlite")
            catalog = catalog_module.ZimCatalog(db, str(zims))
            catalog.scan()
            catalog.close()

            # The drive is unmounted: scanning must fail without deleting rows.
            catalog = catalog_module.ZimCatalog(db, str(root / "unmounted"))
            with self.assertRaises(FileNotFoundError):
                catalog.scan()
            self.assertEqual(len(catalog.rows()), 1)
            catalog.close()

    def test_duplicate_uuid_is_published_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, zims = self._layout(tmp)
            original = zims / "content" / "manual.zim"
            _create_zim(original)
            (zims / "content" / "manual-copy.zim").write_bytes(
                original.read_bytes())
            catalog = catalog_module.ZimCatalog(
                str(root / "catalog.sqlite"), str(zims))
            catalog.scan()

            zims_installed, path_to_id = catalog.book_dict()
            self.assertEqual(len(zims_installed), 1)
            self.assertEqual(list(path_to_id), ["content/manual.zim"])

            library = zims / "library.opds"
            self.assertEqual(catalog.write_opds(str(library)), 1)
            self.assertEqual(library.read_text().count("<entry>"), 1)

            library_xml = zims / "library.xml"
            self.assertEqual(catalog.write_xml(str(library_xml)), 1)
            self.assertEqual(library_xml.read_text().count("<book "), 1)
            catalog.close()

    def test_mtime_change_reopens_the_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, zims = self._layout(tmp)
            zim = zims / "content" / "manual.zim"
            _create_zim(zim)
            catalog = catalog_module.ZimCatalog(
                str(root / "catalog.sqlite"), str(zims))
            catalog.scan()
            later = time.time() + 60
            import os
            os.utime(zim, (later, later))
            self.assertEqual(catalog.scan()["updated"], 1)
            catalog.close()

    def test_invalid_zim_is_omitted_and_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, zims = self._layout(tmp)
            _create_zim(zims / "content" / "manual.zim")
            (zims / "content" / "broken.zim").write_bytes(b"not a zim")
            catalog = catalog_module.ZimCatalog(
                str(root / "catalog.sqlite"), str(zims))
            self.assertEqual(catalog.scan()["invalid"], 1)
            self.assertEqual(len(catalog.book_dict()[0]), 1)
            # The invalid file is not cached, so it is retried next time.
            self.assertEqual(catalog.scan()["invalid"], 1)
            catalog.close()

    def test_foreign_schema_is_rebuilt(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "catalog.sqlite"
            db = sqlite3.connect(db_path)
            db.execute("CREATE TABLE zims (path TEXT PRIMARY KEY, stem TEXT)")
            db.execute(
                "PRAGMA user_version = %d" % catalog_module.SCHEMA_VERSION)
            db.commit()
            db.close()

            catalog = catalog_module.ZimCatalog(str(db_path))
            columns = {
                row["name"]
                for row in catalog._connection().execute(
                    "PRAGMA table_info(zims)")
            }
            self.assertEqual(columns, set(catalog_module._SCHEMA_COLUMNS))
            catalog.close()


if __name__ == "__main__":
    unittest.main()
