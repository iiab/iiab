### Transition to NGINX

1. Initial testing strategy (December 2019 - February 2020) is to move NGINX to [port 80](https://github.com/iiab/iiab/wiki/IIAB-Networking#list-of-ports--services), and proxy everything to Apache on [port 8090](https://github.com/iiab/iiab/wiki/IIAB-Networking#list-of-ports--services) &mdash; creating "Shims" for each IIAB App/Service in *Section iii.* below.

   Until "Native" NGINX is later implemented for that IIAB App/Service &mdash; allowing it to move up to *Section ii.* below.

   And potentially later moving it up to *Section i.* if its Apache support is dropped!
   
   (Background: IIAB Apps/Services are generally [Ansible roles](https://github.com/iiab/iiab/wiki/IIAB-Contributors-Guide#ansible) that live in [/opt/iiab/iiab/roles](https://github.com/iiab/iiab/tree/master/roles))

2. Without PHP available via FastCGI, any function at all for PHP-based applications validates NGINX.

3. Current state of IIAB App/Service migrations as of 2020-03-26:

   1. These support "Native" NGINX but ***NOT*** Apache
      * Admin Console
      * captiveportal
      * IIAB documentation (http://box/info)
      * osm-vector-maps
      * OER2Go/RACHEL modules
      * usb_lib

   2. These support "Native" NGINX ***AND*** Apache, a.k.a. "dual support" for legacy testing (if suitable "Shims" from *Section iii.* below are preserved!)  Both "Native" NGINX and "Shim" proxying from NGINX to Apache port 8090 *cannot be enabled simultaneously* for these IIAB Apps/Service.  But if you want to attempt their "Shim" proxying legacy testing mode, change your *primary web server* over to Apache by setting `nginx_enabled: False` in [/etc/iiab/local_vars.yml](http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F) (which will [auto-enable Apache](../0-init/tasks/main.yml#L40-L44) for your testing).
      * awstats
      * calibre-web
      * gitea
      * kiwix
      * kolibri
      * mediawiki
      * munin
      * nextcloud
      * sugarizer
      * wordpress

   3. These support Apache but ***NOT*** "Native" NGINX.  They use a "Shim" to [proxy_pass](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/) from NGINX to Apache on port 8090.  See [roles/0-init/tasks/main.yml#L40-L44](../0-init/tasks/main.yml#L40-L44) for a list of these IIAB Apps/Services, that auto-enable Apache.
      * elgg
      * lokole
      * moodle
      * nodered

   4. These each run their own web server or non-web / backend services, e.g. off of their own [unique port(s)](https://github.com/iiab/iiab/wiki/IIAB-Networking#list-of-ports--services) (IIAB home pages link directly to these destinations).  In future we'd like mnemonic URL's for all of these: (e.g. http://box/calibre, http://box/archive, http://box/kalite)
      * calibre (menu goes directly to port 8080) [*]
      * internetarchive (menu goes directly to port 4244, [PR #2120](https://github.com/iiab/iiab/pull/2120)) [*]
      * kalite (menu goes directly to ports 8006-8008)
      * minetest [*]
      * openvpn
      * pbx [*]
      * transmission [*]

[*] The 5 above starred roles could use improvement, as of 2020-03-26.
