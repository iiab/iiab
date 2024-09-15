# Nextcloud README

Students and teachers can store their documents, calendars, contacts and photos locally within [Nextcloud](https://nextcloud.com), which is much like having a (local) version of Dropbox or Google Drive on your very own [Internet-in-a-Box](https://internet-in-a-box.org).

This Ansible playbook was derived from an earlier ownCloud playbook thanks to [Josh Dennis](https://github.com/floydianslips) in 2016/2017.

## What's Included

The Nextcloud suite is divided into three main categories:

- [Nextcloud Files](https://nextcloud.com/files/) &ndash; Enterprise File Sync and Share
- [Nextcloud Talk](https://nextcloud.com/talk/) &ndash; Calls, chat and web meetings
- [Nextcloud Groupware](https://nextcloud.com/groupware/) &ndash; Calendar, Contacts & Mail

## Install It

(1) Set these 2 variable in [/etc/iiab/local_vars.yml](http://FAQ.IIAB.IO#What_is_local_vars.yml_and_how_do_I_customize_it%3F) prior to installing Internet-in-a-Box:

    nextcloud_install: True
    nextcloud_enabled: True

<strike>(2) If you want to access Nextcloud from IPv4 addresses across the public Internet, then also set:

    nextcloud_allow_public_ips: True

To further refine Nextcloud access controls based on IPv4 addresses, you can edit `/etc/apache2/sites-available/nextcloud.conf` _after_ it's created by this template: [/opt/iiab/iiab/roles/nextcloud/templates/nextcloud.conf.j2](https://github.com/iiab/iiab/blob/master/roles/nextcloud/templates/nextcloud.conf.j2)</strike>

(3) Be aware of `nginx_high_php_limits: True` in your /etc/iiab/local_vars.yml, which allocates important RAM/resources to PHP, and is effectively auto-enabled for Nextcloud ([PR #3624](https://github.com/iiab/iiab/pull/3624)).  Verify that your Internet-in-a-Box server has enough RAM and disk!  And _after_ Nextcloud is installed, verify and evaluate these 6 settings in `/etc/php/[ACTUAL PHP VERSION]/fpm/php.ini` to be sure:

- upload_max_filesize
- post_max_size
- memory_limit (Nextcloud recommends 512+ MB)
- max_execution_time
- max_input_time
- max_input_vars (Moodle 3.11+ requires 5000+ with PHP 8+)

FYI IIAB will also update `/etc/php/[ACTUAL PHP VERSION]/cli/php.in` (as Moodle requires).

Useful PHP recommendations for these settings (while largely tailored to WordPress, and aimed at very low-end hardware) can be found here: [/opt/iiab/iiab/roles/www_options/tasks/php-settings.yml#L55-L110](../www_options/tasks/php-settings.yml#L55-L110)

(4) Verify system requirements and recommendations for the [latest version Nextcloud](https://github.com/nextcloud/server/wiki/Maintenance-and-Release-Schedule):

- https://docs.nextcloud.com/server/latest/admin_manual/installation/system_requirements.html
- https://docs.nextcloud.com/server/latest/admin_manual/installation/source_installation.html#prerequisites-for-manual-installation
- https://docs.nextcloud.com/server/30/admin_manual/installation/source_installation.html#prerequisites-for-manual-installation
- https://github.com/iiab/iiab/blob/master/roles/nextcloud/tasks/install.yml

## Using It

Log in to Nextcloud at http://box/nextcloud, http://box.lan/nextcloud, http://10.10.10.10/nextcloud (or similar) using:

    Username: Admin
    Password: changeme

## Known Issues

Do not install the [Nextcloud News](https://apps.nextcloud.com/apps/news) app (an RSS/Atom Feed reader) if your OS is 32-bits: [#3069](https://github.com/iiab/iiab/issues/3069)

## Future Directions

Going forward, should Internet-in-a-Box consider integrating optimizations (or more!) from these below?

- ~https://ownyourbits.com/nextcloudpi/~
- ~https://ownyourbits.com/2017/02/13/nextcloud-ready-raspberry-pi-image/~
- https://github.com/nextcloud/nextcloudpi

Please [contact us](https://internet-in-a-box.org/contributing.html) if you can help!
