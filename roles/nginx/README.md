### Transition to NGINX

1. Initial testing strategy is to move NGINX to port 80, and proxy everything to Apache on port 8090 &mdash; creating "Shims" for each IIAB app/service/playbook in *Section iii.* below.

   Until "Native" NGINX is later implemented for that IIAB app/service/playbook &mdash; allowing it to move up to *Section ii.* below.

   And potentially later moving it up to *Section i.* if its Apache support is dropped!

2. Without PHP available via FastCGI, any function at all for PHP-based applications validates NGINX.

3. Current state as of 2020-01-23...

   1. Supports "Native" NGINX but ***NOT*** Apache
      * Admin Console
      * captiveportal
      * osm-vector-maps
      * RACHEL-like modules
      * usb-lib

   2. Supports "Native" NGINX ***AND*** Apache, a.k.a. "dual support" for legacy testing, which can be attempted by setting 'nginx_enabled: False' in /etc/iiab/local_vars.yml (if "Shims" from *Section iii.* below are preserved!)
      * awstats
      * calibre-web
      * gitea
      * kiwix
      * kolibri
      * mediawiki
      * munin
      * sugarizer
      * wordpress

   3. Supports Apache but ***NOT*** NGINX, proxied by an NGINX "Shim" (see [roles/0-init/tasks/main.yml#L39-L49](../0-init/tasks/main.yml#L39-L49) for a list of those IIAB apps/services that auto-enable Apache)
      * dokuwiki ([#2056](https://github.com/iiab/iiab/issues/2056))
      * elgg
      * lokole
      * moodle
      * nextcloud ([PR #2119](https://github.com/iiab/iiab/pull/2119))
      * nodered

   4. Not Yet Dealt With!
      * internetarchive (menu goes directly to port 4244, [PR #2120](https://github.com/iiab/iiab/pull/2120))
      * kalite (menu goes directly to ports 8006-8008)
