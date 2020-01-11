### Transition to NGINX

1. Initial testing strategy is to move nginx to port 80, and proxy everything to Apache on port 8090 -- creating a shim.
2. Without PHP available via FastCGI, any function at all for PHP-based applications validates NGINX.
3. Current state (2020-01-11)
   1. Principal functions migrated to NGINX
      * Admin Console (http://box.lan/admin)
      * kalite -- goes directly to port 8009
      * osm-vector-maps
      * usb-lib
   2. Dual support
      * awstats
      * calibre-web
      * gitea
      * kiwix -- goes directly to port 3000
      * kolibri
      * mediawiki
      * sugarizer
      * wordpress
   3. Still proxied to Apache
      * dokuwiki
      * elgg
      * lokole
      * moodle
      * nodered
      * nextcloud
   4. Not dealt with yet
      * internetarchive
