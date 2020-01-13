### Transition to NGINX

1. Initial testing strategy is to move NGINX to port 80, and proxy everything to Apache on port 8090 -- creating a shim.

2. Without PHP available via FastCGI, any function at all for PHP-based applications validates NGINX.

3. Current state (2020-01-12).

   1. Principal functions migrated to only NGINX
      * Admin Console
      * osm-vector-maps
      * usb-lib

   2. Dual support
      * awstats ([#2124](https://github.com/iiab/iiab/issues/2124))
      * calibre-web
      * gitea
      * kiwix
      * kolibri
      * mediawiki
      * munin
      * rachel
      * sugarizer
      * wordpress

   3. Still proxied to Apache, see [roles/0-init/tasks/main.yml#L108-L112](../0-init/tasks/main.yml#L108-L112)
      * dokuwiki ([#2056](https://github.com/iiab/iiab/issues/2056))
      * elgg
      * lokole
      * moodle
      * nodered
      * nextcloud ([PR #2119](https://github.com/iiab/iiab/pull/2119))

   4. Not yet dealt with
      * internetarchive ([PR #2120](https://github.com/iiab/iiab/pull/2120)) menu uses port
      * kalite  menu goes directly to ports 8006-8008
