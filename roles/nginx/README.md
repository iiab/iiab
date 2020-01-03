### Transition to NGINX
1. Initial testing strategy is to move nginx to port 80, and proxy everything to apache on port 8090-- creating a shim.
2. Without php available via fastcgi, any function at all for php based applications validates nginx.
3. Current state (10/16/19)
    1. Principal functions migrated to nginx.
         * Admin Console
         * Awstats
         * kalite -- goes directly to port 8009
         * usb-lib
         * maps
    2. Dual support
         * kiwix -- goes directly to port 3000
         * calibre-web
         * kolibri
         * sugarizer
    3. Still proxied to Apache
         * mediawiki
         * elgg
         * nodered
         * nextcloud
         * wordpress
         * moodle
    4. Not dealt with yet
         * archive.org
