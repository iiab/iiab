#!/usr/bin/python3

"""

   Rebuild the IIAB ZIM catalog and the kiwix-serve library file.

   The ZIM directory is the source of truth.  Metadata is cached in
   catalog.sqlite; only new or resized ZIMs are reopened.  Invalid ZIMs are
   skipped with a warning.  The library file is written atomically in the
   format supported by the installed kiwix-serve (OPDS for libkiwix 14.3+,
   classic XML for older releases).

   Author: Tim Moody <tim(at)timmoody(dot)com>
   Contributors: Jerry Vonau <jvonau3(at)gmail.com>

"""

import argparse
import hashlib
import json
import logging
import os
import sys
import tempfile

import iiab.iiab_lib as iiab
import iiab.iiab_zim_catalog as zim_catalog

try:
    import iiab.adm_lib as adm
    adm_cons_installed = True
except Exception:
    adm_cons_installed = False


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format='%(levelname)s: %(message)s')

    # Fail loudly rather than silently producing an empty catalog.
    try:
        import libzim    # noqa: F401
    except ImportError:
        print('ERROR: python3-libzim is required (apt install python3-libzim)')
        return 1

    zim_path = iiab.CONST.zim_path
    if args.device:    # allow override of path, e.g. /media/usb0
        zim_path = args.device + zim_path

    catalog_path = args.catalog
    if not catalog_path:
        if args.json:
            # A --json scan (used for USB devices) must not write to the device.
            # Keep a per-device cache in /tmp so unchanged ZIMs are still skipped.
            digest = hashlib.sha1(zim_path.encode('utf-8')).hexdigest()[:12]
            catalog_path = os.path.join(
                tempfile.gettempdir(), 'iiab-zim-catalog-%s.sqlite' % digest)
        else:
            catalog_path = os.path.join(zim_path, zim_catalog.CATALOG_FILENAME)

    if args.library:
        library_path = args.library
    elif args.device:
        library_path = os.path.join(zim_path, zim_catalog.LIBRARY_FILENAME)
    else:
        library_path = getattr(
            iiab.CONST, 'kiwix_library_path',
            os.path.join(zim_path, zim_catalog.LIBRARY_FILENAME))

    catalog = zim_catalog.ZimCatalog(catalog_path, zim_path,
                                     verbose=args.verbose)
    try:
        stats = catalog.scan(force=args.force)

        if args.json:
            zims, _ = catalog.book_dict()
            try:
                json.dump(zims, sys.stdout)
                sys.stdout.write('\n')
            except BrokenPipeError:
                pass
            return 0

        # If the directory has ZIMs but none could be read, keep the previous
        # library rather than replacing it with an empty one.
        if stats['total'] > 0 and not catalog.rows():
            print('ERROR: none of the %d ZIM files could be read; '
                  'keeping the previous library' % stats['total'])
            return 1

        fmt = args.format
        if fmt == 'auto':
            kiwix_serve = getattr(iiab.CONST, 'kiwix_serve', None)
            if not kiwix_serve:
                kiwix_serve = os.path.join(
                    getattr(iiab.CONST, 'iiab_base_path', '/opt/iiab'),
                    'kiwix', 'bin', 'kiwix-serve')
            fmt = zim_catalog.detect_library_format(kiwix_serve)

        if fmt == 'opds':
            count = catalog.write_opds(library_path)
        else:
            count = catalog.write_xml(library_path)

        # Remove the pre-OPDS file only after the new one has been written.
        legacy = os.path.join(zim_path, 'library.xml')
        if os.path.abspath(legacy) != os.path.abspath(library_path):
            try:
                os.remove(legacy)
                print('Removed legacy %s' % legacy)
            except OSError:
                pass

        if args.verbose:
            print('Wrote %s (%s, %d books) from %s'
                  % (library_path, fmt, count, catalog_path))
            print('Catalog stats: %s' % stats)

        # Create zim_versions_idx if the Admin Console is installed.
        # (Never do this for --device: that catalog belongs to another box.)
        # This is a UI projection, not part of the catalog: a failure must not
        # make the freshly written library look like a failed build.
        if adm_cons_installed and not args.device:
            print('Writing zim_versions_idx')
            try:
                iiab.read_lang_codes()
                zim_files, zim_versions = iiab.get_zim_list(zim_path)
                zim_menu_defs = adm.get_zim_menu_defs()
                adm.write_zim_versions_idx(
                    zim_versions, library_path,
                    adm.CONST.zim_version_idx_dir, zim_menu_defs)
            except Exception as error:
                print('Warning: failed to write zim_version_idx.json: %s'
                      % error)
        return 0
    finally:
        catalog.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description='Create the IIAB ZIM catalog and kiwix library file.')
    parser.add_argument('--device',
                        help='no trailing /. change the target device from '
                             'internal storage to something else like /media/usb0')
    parser.add_argument('--no_tmp',
                        help='deprecated no-op (the library is written atomically)',
                        action='store_true')
    parser.add_argument('-f', '--force',
                        help='reopen every ZIM, even if its size is unchanged',
                        action='store_true')
    parser.add_argument('--format', choices=('auto', 'opds', 'xml'),
                        default='auto',
                        help='library format; auto uses the installed libkiwix version')
    parser.add_argument('--catalog',
                        help='catalog cache path (default: <zim-path>/catalog.sqlite)')
    parser.add_argument('--library',
                        help='library file to write (default: iiab_const.kiwix_library_path)')
    parser.add_argument('--json',
                        help='print the installed ZIM dict as JSON and do not '
                             'write a library file (used for USB devices)',
                        action='store_true')
    parser.add_argument('-v', '--verbose', help='Print messages.',
                        action='store_true')
    return parser.parse_args()


# Now start the application
if __name__ == "__main__":
    sys.exit(main())
