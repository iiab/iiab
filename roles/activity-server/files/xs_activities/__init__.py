# Copyright (C) 2008 One Laptop Per Child Association, Inc.
# Licensed under the terms of the GNU GPL v2 or later; see COPYING for details.
#
# written by Douglas Bagnall <douglas@paradise.net.nz>

"""Functions for processing XO activities, either for indexing and
presentaton to the laptops, or for diagnostics.
"""

import os, sys, shutil
import zipfile
import re
from cStringIO import StringIO
#import traceback
import syslog
from ConfigParser import SafeConfigParser

# we no longer really have a default in that it is set in the conf file
# we assume that we have a lang_template for the default language
TEMPLATE_DIR = '/library/xs-activity-server/lang_templates'
DEFAULT_LANG = 'en'

# how many versions before the latest are worth having around.
KEEP_OLD_VERSIONS = 3

#print to stderr, rathe than syslog?
USE_STDERR=False

REQUIRED_TAGS = ('bundle_id', 'activity_version', 'host_version', 'name', 'license')
OPTIONAL_TAGS = ('show_launcher', 'exec', 'mime_types', 'icon')
#XXX need either icon or show_launcher=no

def log(msg, level=syslog.LOG_NOTICE):
    if USE_STDERR:
        print >> sys.stderr, msg
    else:
        syslog.openlog( 'xs-activity-server', 0, syslog.LOG_USER )
        syslog.syslog(level, msg)
        syslog.closelog()

class BundleError(Exception):
    pass

class Bundle(object):
    def __init__(self, bundle):
        self.linfo = {}
        self.zf = zipfile.ZipFile(bundle)
        # The activity path will be 'Something.activity/activity/activity.info'
        for p in self.zf.namelist():
            if p.endswith(self.INFO_PATH):
                self.raw_data = read_info_file(self.zf, p, self.INFO_SECTION)

        # the file name itself is needed for the URL
        self.url = os.path.basename(bundle)
        self.mtime = os.stat(bundle).st_mtime

        self.name = self.raw_data.get('name')
        self.license = self.raw_data.get('license', None)

        # child ctor should now call
        # _set_bundle_id
        # _set_version
        # _set_description
    def _set_bundle_id(self, id):
        if id is None:
            raise BundleError("bad bundle: No bundle ID")
        self.bundle_id = id
        if self.name is None:
            self.name = id

    def _set_version(self, version):
        self.version = version

    def _set_description(self, description):
        self.description = description

    def __cmp__(self, other):
        """Alphabetical sort (locale dependant of course)"""
        if self.bundle_id == other.bundle_id:
            return cmp(self.version, other.version)
        return cmp(self.name, other.name)

    def set_older_versions(self, versions):
        """Versions should be a list of (version number, version tuples)"""
        self.older_versions = ', '.join('<a href="%s">%s</a>' % (v.url, v.version) for v in versions)

    def to_html(self, locale, template=None):
        """Fill in the template with data approriate for the locale."""
        if template is None:
            template = read_template('activity', locale)

        d = {'older_versions':      self.older_versions,
             'bundle_id':           self.bundle_id,
             'activity_version':    self.version,
             'bundle_url':          self.url,
             'name':                self.name,
             'description':         self.description,
             }

        d.update(self.linfo.get(locale, {}))

        if d['older_versions']:
            d['show_older_versions'] = 'inline'
        else:
            d['show_older_versions'] = 'none'

        return template % d

    def get_name(self, locale=None):
        return self.name

class Content(Bundle):
    INFO_PATH = "library/library.info"
    INFO_SECTION = "Library"

    def __init__(self, bundle):
        super(Content, self).__init__(bundle)

        d = self.raw_data
        # bundle_id is often missing; service name is used instead.
        self._set_bundle_id(d.get('global_name', None))
        self._set_version(d.get('library_version', 1))
        self._set_description(d.get('long_name', ''))

    def debug(self, force_recheck=False):
        # FIXME: implement debug checking for content bundles
        return {}

class Activity(Bundle):
    INFO_PATH = "activity/activity.info"
    INFO_SECTION = "Activity"

    #Activities appear to be looser than RFC3066, using e.g. _ in place of -.
    linfo_re = re.compile(r'/locale/([A-Za-z]+[\w-]*)/activity.linfo$')

    def __init__(self, bundle):
        """Takes a zipped .xo bundle name, returns a dictionary of its
        activity info.  Can raise a variety of exceptions, all of
        which should indicate the bundle is invalid."""
        super(Activity, self).__init__(bundle)

        # The locale info will be Something.activity/locale/xx_XX/activity.linfo
        for p in self.zf.namelist():
            linfo = self.linfo_re.search(p)
            if linfo:
                lang = canonicalise(linfo.group(1))
                self.linfo[lang] = read_info_file(self.zf, p, self.INFO_SECTION)

        # Unfortunately the dictionary lacks some information, and
        # stores other bits in inconsistent ways.

        d = self.raw_data
        # bundle_id is often missing; service name is used instead.
        self._set_bundle_id(d.get('bundle_id', d.get('service_name')))
        self._set_version(d.get('activity_version', 1))
        self._set_description(d.get('description', ''))

    def debug(self, force_recheck=False):
        """Make a copy of the raw data with added bits so we can work
        out what is going on.  This is useful for diagnosing problems
        with odd activities and composing tut-tut-ing emails to their
        authors.

        Not used in production."""
        if hasattr(self, '_debug_data') and not force_recheck:
            return self._debug_data

        d = self.raw_data.copy()

        correct_forms = {
            'name': str.upper,
            'activity_version': str.isdigit,
            'host_version': str.isdigit,
            'bundle_id': re.compile(r'^[\w.]+$').match,
            'service_name': re.compile(r'^[\w.]+$').match,
            'icon': re.compile(r'^[\S]+$').match,
            'exec': str.upper,
            'mime_types': re.compile(r'^([\w.+-]+/[\w.+-]+;?)*$').match,
            'update_url': re.compile(r'^http://([\w-]+\.?)+(:\d+)?(/[\w~%.-]+)*$').match,
            #'update_url': re.compile(r'^$').match,
            'show_launcher': re.compile(r'^(yes)|(no)$').match,
            'class': re.compile(r'^(\w+.?)+$').match,
            'license': str.upper,
            #'license': re.compile(r'^GPLv[23]\+?$').match,
            }

        for k, v in d.items():
            if k in correct_forms:
                f = correct_forms.get(k, len)
                if not f(v):
                    d['BAD ' + k] = v

        rcount = 0
        for k in REQUIRED_TAGS:
            if k not in d:
                d['LACKS %s' % k] = True
                rcount += 1
        d['MISSING KEYS'] = rcount

        for t in OPTIONAL_TAGS:
            if t not in d:
                d['NO ' + t] = True

        if  not 'icon' in d and d.get('show_launcher') != 'no':
            d['NO icon AND show_launcher'] = True

        self._debug_data = d
        return d

    def get_name(self, locale):
        """Return the best guess at a name for the locale."""
        for loc in locale_search_path(locale):
            if loc in self.linfo and 'name' in self.linfo[loc]:
                return self.linfo[loc]['name']
        return super(Activity, self).get_name()



def check_all_bundles(directory, show_all_bundles=False):
    """A verbose debug function."""
    all_bundles = []
    unique_bundles = {}
    counts = {}
    # watch for these tags and print out the lists
    bad_contents = {}
    all_linfo = {}
    unique_linfo = {}
    linfo_keys = {}
    log('Checking all activities in %s\n' % directory)
    for f in os.listdir(directory):
        if not f.endswith('.xo') and not f.endswith('.xol'):
            continue
        #log(f)
        try:
            if f.endswith('.xo'):
                bundle = Activity(os.path.join(directory, f))
            else:
                bundle = Content(os.path.join(directory, f))
        except Exception, e:
            log("IRREDEEMABLE bundle %-25s (Error: %s)" % (f, e), syslog.LOG_WARNING)

        #Clump together bundles of the same ID
        x = unique_bundles.setdefault(bundle.bundle_id, [])
        x.append(bundle)
        all_bundles.append(bundle)

    if not show_all_bundles:
        #only show the newest one of each set.
        bundles = []
        for versions in unique_bundles.values():
            versions.sort()
            bundles.append(versions[-1])

    else:
        bundles = all_bundles

    licenses = {}
    for bundle in bundles:
        bid = bundle.bundle_id
        for k, v in bundle.debug().iteritems():
            counts[k] = counts.get(k, 0) + 1
            if k.startswith('BAD '):
                bc = bad_contents.setdefault(k, {})
                bc[bid] = v
        for k, v in bundle.linfo.iteritems():
            linfo_l = all_linfo.setdefault(k, [])
            linfo_l.append(bundle)
            for x in v:
                linfo_keys[x] = linfo_keys.get(x, 0) + 1
            if v['name'] != bundle.name:
                linfo_l = unique_linfo.setdefault(k, [])
                linfo_l.append(bundle)

        if bundle.license:
            lic = licenses.setdefault(bundle.license, [])
            lic.append(bundle.bundle_id)

    citems = counts.items()
    rare_keys = [k for k, v in citems if v < 10]
    lack_counts = dict((k, v) for k, v in citems if k.startswith('LACKS '))
    bad_counts = dict((k, v) for k, v in citems if k.startswith('BAD '))
    no_counts = dict((k, v) for k, v in citems if k.startswith('NO '))
    tag_counts = dict((k, v) for k, v in citems if k not in lack_counts and
                      k not in bad_counts and k not in no_counts and k != 'MISSING KEYS')

    # flag whether the tag is needed, ok, or not
    tag_quality = dict((k, '*') for k in REQUIRED_TAGS)
    tag_quality.update((k, '+') for k in OPTIONAL_TAGS)
    linfo_counts = dict((k, len(v)) for k, v in all_linfo.iteritems())
    linfo_uniq_counts = dict((k, len(v)) for k, v in unique_linfo.iteritems())

    log('\nFound: %s bundles\n       %s unique bundles' % (len(all_bundles), len(unique_bundles)))
    for d, name, d2 in [(tag_counts, '\nattribute counts:', tag_quality),
                        (lack_counts, '\nmissing required keys:', {}),
                        (no_counts, '\nunused optional keys:', {}),
                        (bad_counts, '\nill-formed values:', {}),
                        (linfo_counts, '\nlinfo counts:             total  localised', linfo_uniq_counts),
                        (linfo_keys, '\nlinfo keys:', {})]:
        log(name)
        counts_reversed = [(v, k) for (k, v) in d.iteritems()]
        counts_reversed.sort()
        counts_reversed.reverse()
        for (k, v) in counts_reversed:
            log("%-25s %4s   %4s" % (v, k, d2.get(v, '')))

    log("\nRare keys:")
    for k in rare_keys:
        if k.startswith('BAD '):
            continue
        log(k)
        for b in bundles:
            v = b.debug().get(k)
            if v:
                log('      %-25s %s' % (b.bundle_id, v))


    log("\nInteresting contents:")
    for k, v in bad_contents.iteritems():
        log(k)
        for x in v.iteritems():
            log('      %s: %s' % x)

    log("\nInteresting linfo:")
    for k in ('pseudo',):
        log(k)
        for a in all_linfo[k]:
            if a in unique_linfo.get(k, []):
                log('   *  %s  (%s vs. %s)' % (a.bundle_id, a.name, a.linfo[k]['name']))
            else:
                log('      %s (%s)' % (a.bundle_id, a.name))

    log("\nLicenses:")
    for lic, v in licenses.iteritems():
        log("%-20s  %s" %(repr(lic), len(v)))

    log("\nRare licenses:")
    for lic, v in licenses.iteritems():
        if len(v) < 3:
            log('   %s' % lic)
            for x in v:
                log("      %s" %(x))



    log("\nAlmost valid activities:")
    for b in bundles:
        d = b.debug()
        if d['MISSING KEYS'] == 1:
            missing = ', '.join(x for x in d if x.startswith('LACKS'))
            bad_values = ', '. join(x for x in d if x.startswith('BAD'))
            log("%-20s %s %s" %(b.name, missing, bad_values))

    log("\nValid activities (maybe):")
    for b in bundles:
        d = b.debug()
        bid = b.bundle_id
        if (d['MISSING KEYS'] == 0 and
            bid not in bad_contents['BAD mime_types']):
            log("%-20s - %s" %(b.name, bid))
            #log(a.raw_data)




def read_info_file(zipfile, path, section):
    """Return a dictionary matching the contents of the config file at
    path in zipfile"""
    cp = SafeConfigParser()
    info = StringIO(zipfile.read(path))
    cp.readfp(info)
    return dict(cp.items(section))

def canonicalise(lang):
    """Make all equivalent language strings the same.
    >>> canonicalise('Zh-cN')
    zh-CN
    >>> canonicalise('zh_CN')
    zh-CN
    """
    lang = lang.replace('_', '-').upper()
    bits = lang.split('-', 1)
    bits[0] = bits[0].lower()
    return '-'.join(bits)

def locale_search_path(locale):
    """Find a series of sensible locales to try, including
    DEFAULT_LANG. For example 'zh-CN' would become ('zh-CN', 'zh',
    'DEFAULT_LANG')."""
    #XXX might be better to be storing locale as tuple
    if '-' in locale:
        return (locale, locale.split('-')[0], DEFAULT_LANG)
    return (locale, DEFAULT_LANG)



def read_metadata(bundle_dir):
    """Attempt to read data in a metadata file. Raises expected
    exceptions if the metadata file isn't readable. The file should
    look something like this:

    [org.laptop.Pippy]
    description = Succinct description of this activity.

    [org.laptop.Develop]
    description = Succinct description of this activity.
    web_icon = develop.png
    """
    md_files = [os.path.join(bundle_dir, x)
               for x in os.listdir(bundle_dir) if x.endswith('.info')]
    cp = SafeConfigParser()
    cp.read(md_files)
    metadata = {}
    for section in cp.sections():
        metadata[section] = dict(x for x in cp.items(section))
    return metadata


def htmlise_bundles(bundle_dir, dest_html):
    """Makes a nice html manifest for the bundles in a directory.  The
    manifest only shows the newest version of each bundle.
    """
    #so, we collect up a dictionary of lists, then sort each list on
    #the version number to find the newest.

    bundles = [os.path.join(bundle_dir, x)
               for x in os.listdir(bundle_dir) if x.endswith('.xo') or x.endswith('.xol')]

    try:
        metadata = read_metadata(bundle_dir)
    except Exception, e:
        log("had trouble reading metadata: %s" % e)
        metadata = {}

    all_bundles = {}
    for filename in bundles:
        try:
            if filename.endswith('.xo'):
                bundle = Activity(filename)
            else:
                bundle = Content(filename)
            x = all_bundles.setdefault(bundle.bundle_id, [])
            x.append((bundle.mtime, bundle))
        except Exception, e:
            log("Couldn't find good activity/library info in %s (Error: %s)" % (filename, e))

    newest = []
    # create an index for each language that has a template
    # but track any locales in bundles in case we do not have templates for them
    locales = [os.path.join(o) for o in os.listdir(TEMPLATE_DIR) if os.path.isdir(os.path.join(TEMPLATE_DIR,o))]
    locales_found = set ()
    for versions in all_bundles.values():
        versions = [x[1] for x in sorted(versions)]
        # end of list is the newest; beginning of list might need deleting
        latest = versions.pop()
        locales_found.update(latest.linfo)
        newest.append(latest)
        goners = versions[:-KEEP_OLD_VERSIONS]
        keepers = versions[-KEEP_OLD_VERSIONS:]
        for v in goners:
            fn = os.path.join(bundle_dir, v.url)
            os.remove(fn)
        latest.set_older_versions(keepers)

        if latest.bundle_id in metadata:
            # we have extra metadata with which to fill out details
            # presumably this is mainly human-oriented description.
            d = metadata[latest.bundle_id]
            for k in ('description', 'name'):
                if k in d:
                    setattr(latest, k, d[k])

    log('found locales: %s' % locales)
   
    # assume locales is not empty as we have at least the default language
    for locale in locales:
        try:
            make_html(newest, locale, '%s.%s' % (dest_html, locale))
        except Exception, e:
            log("Couldn't make page for %s (Error: %s)" % (locale, e), syslog.LOG_WARNING)    
        
    # make_varfile(locales, dest_html)- have switched to multiviews, so var not needed


def make_varfile(locales, dest_html):
    f = open(dest_html + '.var', 'w')
    index = os.path.basename(dest_html)
    f.write('URI: %s\n\n' % index)
    for locale in locales:
        f.write('URI: %s.%s\n' % (index, locale))
        f.write('Content-type: text/html; charset=utf-8\n')
        f.write('Content-language: %s\n\n' % locale)
    # now the default, slightly higher qs
    f.write('URI: %s.DEFAULT\n' % index)
    f.write('Content-type: text/html; charset=utf-8\n')
    f.write('Content-language: en\n\n')

    f.close()

def read_template(name, locale):
    """Try to read the locale's template, falling back to the
    default."""
    #also try containing locales, eg 'zh' for 'zh-CN'
    for x in locale_search_path(locale):
        try:
            f = open(os.path.join(TEMPLATE_DIR, x, name))
            break
        except (OSError, IOError), e:
            #log(str(e))
            continue
    s = f.read()
    f.close()
    return s


def make_html(bundles, locale, filename):
    """Write a microformated index for the activities in the appropriate language,
    and save it to filename."""
    page_tmpl = read_template('page', locale)
    act_tmpl = read_template('activity', locale)

    #bundles.sort() won't cut it.
    schwartzian = [ (x.get_name(locale), x.to_html(locale, act_tmpl)) for x in bundles ]
    schwartzian.sort()
    s = page_tmpl % {'activities': '\n'.join(x[1] for x in schwartzian)}

    if os.path.exists(filename):
        shutil.move(filename, filename + '~')
    f = open(filename, 'w')
    f.write(s)
    f.close()





