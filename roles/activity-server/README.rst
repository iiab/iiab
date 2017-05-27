Serve XO activities from the XS school server
=============================================

XO laptops can update their activities via HTTP, using specially
microformatted html pages to determine what to download.

This package imports XO activities from a USB stick and generates the
correct html to serve them, in as many languages as it knows how,
using the localisation information from the activity bundles.  Content
negotiation between Apache and the laptops decides what html is seen.

The URL for this index is http://schoolserver/activities/.

A facility exists to add extra descriptive html to the generated
indexes.

USB import
----------

When a USB drive is inserted, the server looks for a directory in the
root directory called xs-activity-server.  In there it expects to find
any number of activity bundles, a file called manifest.sha1, and
optionally a file or files with the suffix ".info".  Depending on the
configuration of the school server, a file called "manifest.sha1.sig"
might also be required.

Activity bundles are zip files with the suffix .xo and an internal
layout described at http://wiki.laptop.org/go/Activity_bundles.

The manifest file should contain sha1sums for each activity bundle and
the metadata files, as if you had run

  sha1sum *.xo *.info > manifest.sha1

in the directory.

If full XS security is enabled (by the presence of /etc/xs-security-on
-- see the xs-tools documentation), then manifest.sha1.sig should
contain a detached GPG signature for manifest.sha1, signed by a key
that the XS knows.  If the school server lacks the /etc/xs-security-on
flag, the manifest.sha1.sig file is ignored.

Multiple languages
------------------

Activities can contain localisation information, which usually
consists of a translated activity name.  The localised information is
found in the bundle in a directory like:

SomeWonderful.activity/locale/pt-BR/activity.linfo

where pt-BR is an RFC1788 language code. If any activity contains an
activity.linfo file for a language, then an index is generated.  The
server has templates for indexes in some languages (currently Spanish
and English); for other languages the indexes will be in English
except for the localised names.

These index files are saved with names like
activities/index.html.zh-es.  You can choose to look at them directly
that way, or let your browser decide which one is best for you by
visiting activities/index.html.

If some activities lack localised information for a multi-part
language code, the index will include information that exists for the
corresponding single part code, before defaulting to English.  For
example, a zh-CN page will include zh localisation if need be.  (This
may not always be the best result: bn and bn-IN appear to use
different scripts).


Including extra descriptions
----------------------------

The optional .info files in the xs-activation-server directory should
consist of sections in this format:

  [com.microsoft.Word]
  description = Write replacement, without distraction of collaboration.

  [some.other.Something]
  description = another description, all on one line.

If a section heading (in square brackets) matches the bundle_id or
service_name of an activity, the description will be displayed on the
generated html page.  This information is not used by automatic
updates, but it might assist children in browsing and manually
installing activities.  Note: there is no clever localisation here.

Multiple versions
-----------------

Over the course of a server deployment, an activity might be updated
several times.  To preserve disk space, only the 4 most recent
versions of an activity are kept.  Links to the second, third and
fourth newest versions are presented in the activities html file, but
these do not use the activity microformat and will not be visible to
automated updaters.

To determine which activities are the most recent, the file's modification
times (mtime) are examined. The version number is not considered here.

Note: If you plug in a USB stick with very out-of-date activities they
will be deleted as soon as they get on the server.

HTML microformat
----------------

The microformat is described at
http://wiki.laptop.org/go/Activity_microformat.

Utility script
--------------

/usr/bin/xs-check-activities will print statistics about a directory
of activities to stderr.  Its output is not particularly well
formatted or explained, but it is there if you want it.

Files and directories
---------------------

Activities are stored in /library/xs-activity-server/activities, with
the html index being index.html in that directory.  Apache is coaxed
into serving this by /etc/httpd/conf.d/xs-activity-server.conf.

Bugs
----

Old versions are only saved if the different versions have different
file names.  Most activity bundles have names like 'Maze-4.xo',
'Maze-5.xo' and so on, but some lack the version number in the file
name, so the most recently imported version ends up overwriting the
older ones.

Source
------

This role is based on the xs-activity-server rpm.

http://dev.laptop.org/git/users/martin/xs-activity-server/ v0.4 release