### Transition to NGINX
1. Initial testing strategy is to move nginx to port 80, and proxy everything to apache on port 8090-- creating a shim.
2. Without php available via fastcgi, any function at all for php based applications validates nginx.
3. Current state (10/16/19)
    1. Principal functions migrated to nginx.
         * Admin Console
         * kalite -- goes directly to port 8009
         * maps
         * usb-lib
    2. Dual support
         * Awstats
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
         * archive.org
