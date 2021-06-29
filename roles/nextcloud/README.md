# Nextcloud

Students and teachers can store their documents, calendars, contacts and photos locally within [Nextcloud](https://nextcloud.com), which is much like having a (local) version of Dropbox or Google Drive on your very own [Internet-in-a-Box](http://internet-in-a-box.org).

This Ansible playbook was derived from an earlier ownCloud playbook thanks to [Josh Dennis](https://github.com/floydianslips) in 2016/2017.

## What's Included

The Nextcloud suite is divided into three main categories:

- [Nextcloud Files](https://nextcloud.com/files/) &ndash; Enterprise File Sync and Share
- [Nextcloud Talk](https://nextcloud.com/talk/) &ndash; Calls, chat and web meetings
- [Nextcloud Groupware](https://nextcloud.com/groupware/) &ndash; Calendar, Contacts & Mail

## Install It

(1) Set these 2 variable in [/etc/iiab/local_vars.yml](http://FAQ.IIAB.IO#What_is_local_vars.yml_and_how_do_I_customize_it.3F) prior to installing Internet-in-a-Box:

    nextcloud_install: True
    nextcloud_enabled: True

<strike>(2) If you want to access Nextcloud from IPv4 addresses across the public Internet, then also set:

    nextcloud_allow_public_ips: True

To further refine Nextcloud access controls based on IPv4 addresses, you can edit `/etc/apache2/sites-available/nextcloud.conf` _after_ it's created by this template: [/opt/iiab/iiab/roles/nextcloud/templates/nextcloud.conf.j2](https://github.com/iiab/iiab/blob/master/roles/nextcloud/templates/nextcloud.conf.j2)</strike>

(3) Strongly consider also setting `nginx_high_php_limits: True` in your /etc/iiab/local_vars.yml, to allocate important RAM/resources to PHP.  Of course, enabling this might cause excess use of RAM/disk or other resources if not calibrated to your hardware and network!  So _after_ install is complete, verify and evaluate these 6 settings in /etc/php/[ACTUAL PHP VERSION]/fpm/php.ini:

- upload_max_filesize
- post_max_size
- memory_limit (Nextcloud recommends 512+ MB)
- max_execution_time
- max_input_time
- max_input_vars (Moodle 3.11+ requires 5000+ with PHP 8+)

Useful PHP recommendations for these settings (while largely tailored to WordPress, and aimed at very low-end hardware) can be found here: [/opt/iiab/iiab/roles/www_options/tasks/main.yml#L53-L133](../www_options/tasks/main.yml#L53-L133)

(4) If you're running Nextcloud 22+ in production, carefully check that Nextcloud's latest formal prereqs (required AND recommended) are included per your community's needs.  In places like these:

- https://docs.nextcloud.com/server/22/admin_manual/installation/source_installation.html#prerequisites-for-manual-installation
- https://github.com/iiab/iiab/blob/master/roles/nextcloud/tasks/install.yml

## Using It

Log in to Nextcloud at http://box/nextcloud, http://box.lan/nextcloud, http://172.18.96.1/nextcloud (or similar) using:

    Username: Admin
    Password: changeme

## Future Directions

Going forward, should Internet-in-a-Box consider integrating optimizations (or more!) from these below?

- https://ownyourbits.com/nextcloudpi/
- https://ownyourbits.com/2017/02/13/nextcloud-ready-raspberry-pi-image/
- https://github.com/nextcloud/nextcloudpi

Please [contact us](http://internet-in-a-box.org/pages/contributing.html) if you can help!
