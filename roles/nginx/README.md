### Transition to NGINX

1. Initial testing strategy is to move NGINX to port 80, and proxy everything to Apache on port 8090 &mdash; creating "Shims" for each IIAB App/Service in *Section iii.* below.

   Until "Native" NGINX is later implemented for that IIAB App/Service &mdash; allowing it to move up to *Section ii.* below.

   And potentially later moving it up to *Section i.* if its Apache support is dropped!

2. Without PHP available via FastCGI, any function at all for PHP-based applications validates NGINX.

3. Current state IIAB App/Service migrations as of 2020-01-23...

   1. These support "Native" NGINX but ***NOT*** Apache
      * Admin Console
      * captiveportal
      * osm-vector-maps
      * RACHEL-like modules
      * usb-lib

   2. These support "Native" NGINX ***AND*** Apache, a.k.a. "dual support" for legacy testing (if suitable "Shims" from *Section iii.* below are preserved!)  Both "Native" NGINX and "Shim" proxying from NGINX to Apache port 8090 *cannot be enabled simultaneously* for these IIAB Apps/Service.  But if you want to attempt their "Shim" proxying legacy testing mode, [auto-enable Apache](../0-init/tasks/main.yml#L40-L44) by setting `nginx_enabled: False` in [/etc/iiab/local_vars.yml](http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F)
      * awstats
      * calibre-web
      * gitea
      * kiwix
      * kolibri
      * mediawiki
      * munin
      * sugarizer
      * wordpress

   3. These support Apache but ***NOT*** "Native" NGINX.  These use a "Shim" to [proxy_pass](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/) from NGINX to Apache on port 8090.  See [roles/0-init/tasks/main.yml#L40-L44](../0-init/tasks/main.yml#L40-L44) for a list of these IIAB Apps/Services, that auto-enable Apache.
      * dokuwiki ([#2056](https://github.com/iiab/iiab/issues/2056))
      * elgg
      * lokole
      * moodle
      * nextcloud ([PR #2119](https://github.com/iiab/iiab/pull/2119))
      * nodered

   4. Not Yet Dealt With!
      * internetarchive (menu goes directly to port 4244, [PR #2120](https://github.com/iiab/iiab/pull/2120))
      * kalite (menu goes directly to ports 8006-8008)
