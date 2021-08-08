### Transition to NGINX

1. Initial testing strategy (December 2019 - February 2020) was to move NGINX to [port 80](https://github.com/iiab/iiab/wiki/IIAB-Networking#list-of-ports--services), and proxy everything to Apache on [port 8090](https://github.com/iiab/iiab/wiki/IIAB-Networking#list-of-ports--services) &mdash; creating "Shims" for each IIAB App/Service in *Section iii.* below.

   Until "Native" NGINX is later implemented for each such IIAB App/Service &mdash; allowing each to move up to *Section ii.* below.

   And potentially later moving each up to *Section i.* if its Apache support is dropped!

   (Background: IIAB Apps/Services are generally [Ansible roles](https://github.com/iiab/iiab/wiki/IIAB-Contributors-Guide#ansible) that live in [/opt/iiab/iiab/roles](https://github.com/iiab/iiab/tree/master/roles))

2. Without PHP available via FastCGI, any function at all for PHP-based applications validates NGINX.

3. Current state of IIAB App/Service migrations as of 2021-08-08: *(SEE ALSO [#2762](https://github.com/iiab/iiab/issues/2762))*

   1. These support "Native" NGINX but ***NOT*** Apache

      * Admin Console
      * awstats
      * calibre-web
      * captiveportal
      * gitea
      * IIAB documentation (http://box/info)
      * jupyterhub
      * kiwix
      * kolibri
      * lokole
      * mediawiki
      * moodle
      * munin
      * nextcloud
      * nodered
      * OER2Go/RACHEL modules
      * osm-vector-maps
      * sugarizer
      * usb_lib
      * wordpress

   2. These support "Native" NGINX ***AND*** Apache, a.k.a. "dual support" for legacy testing (if suitable "Shims" from *Section iii.* below are preserved!)  Both "Native" NGINX and "Shim" proxying from NGINX to Apache port 8090 *cannot be enabled simultaneously* for these IIAB Apps/Service:<!--But if you want to attempt their "Shim" proxying legacy testing mode, try setting your *primary web server* to Apache using `apache_install: True` and `apache_enabled: True` (and `nginx_enabled: False` to disable NGINX) in [/etc/iiab/local_vars.yml](http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F) before you install IIAB.  You may also need to run `cd /opt/iiab/iiab; ./runrole httpd` since this has been removed from [roles/3-base-server/tasks/main.yml](https://github.com/iiab/iiab/blob/master/roles/3-base-server/tasks/main.yml)-->

      * **NONE: Apache support is now fully REMOVED as of 2021-08-08** ([PR #2850](https://github.com/iiab/iiab/pull/2850))

   3. These support Apache but ***NOT*** "Native" NGINX.  They use a "Shim" to [proxy_pass](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/) from NGINX to Apache on port 8090.  See [roles/3-base-server/tasks/main.yml#L11](../3-base-server/tasks/main.yml#L11) for a list of ~6 IIAB Apps/Services that auto-enable Apache.

      * elgg [deprecated -- consider assisting with a complete overhaul from Elgg 2.x to 4.x ?]

   4. These each run their own web server or non-web / backend services, e.g. off of their own [unique port(s)](https://github.com/iiab/iiab/wiki/IIAB-Networking#list-of-ports--services) (IIAB home pages link directly to these destinations).  In future we'd like mnemonic URL's for all of these: (e.g. http://box/calibre, http://box/archive, http://box/kalite)

      * bluetooth
      * calibre (menu goes directly to port 8080)
      * cups (NGINX redirects http://box/print to port 631, changing URL hostname to localhost when necessary, per [PR #2858](https://github.com/iiab/iiab/pull/2858))
      * internetarchive (menu goes directly to port 4244) [*, [PR #2120](https://github.com/iiab/iiab/pull/2120)]
      * kalite (menu goes directly to ports 8006-8008)
      * minetest
      * mosquitto
      * openvpn
      * pbx [*, recommends Apache for now, as in Section iii., [#2914](https://github.com/iiab/iiab/issues/2914)]
      * phpmyadmin [*, requires Apache for now, as in Section iii.]
      * samba [*]
      * sshd
      * transmission
      * vnstat

[*] The 4 above starred roles could use improvement, as of 2021-08-08.
