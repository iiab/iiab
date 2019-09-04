# Nextcloud

Students and teachers can store their documents, calendars, contacts and photos locally within [Nextcloud](https://nextcloud.com), which is much like having a (local) version of Dropbox or Google Drive on your very own Internet-in-a-Box.

This Ansible playbook was derived from an earlier ownCloud playbook thanks to [Josh Dennis](https://github.com/floydianslips) in 2016/2017.

### Using It

Administrators verify that Nextcloud is installed on your Internet-in-a-Box (check [/etc/iiab/local_vars.yml](http://FAQ.IIAB.IO#What_is_local_vars.yml_and_how_do_I_customize_it.3F)) and then log in to Nextcloud at http://box/nextcloud, http://box.lan/nextcloud, http://172.18.96.1/nextcloud (or similar) using:

    Username: Admin
    Password: changeme

### Future Directions

Going forward, should Internet-in-a-Box consider integrating optimizations (or more!) from these below?

- https://ownyourbits.com/nextcloudpi/
- https://ownyourbits.com/2017/02/13/nextcloud-ready-raspberry-pi-image/
- https://github.com/nextcloud/nextcloudpi

Please [contact us](http://internet-in-a-box.org/pages/contributing.html) if you can help!
