# CUPS Printing README

[CUPS](https://en.wikipedia.org/wiki/CUPS) (also known as the "Common UNIX Printing System") is the standards-based, open source printing system for Linux and macOS.

It allows your [Internet-in-a-Box (IIAB)](http://internet-in-a-box.org) to act as a print server.

This can be useful if a printer is attached to your IIAB &mdash; so student/teacher print jobs from client computers and phones can be processed &mdash; and then sent to the appropriate printer.

## Using it

Make sure your IIAB was installed with these 2 lines in [/etc/iiab/local_vars.yml](http://faq.iiab.io/#What_is_local_vars.yml_and_how_do_I_customize_it.3F) :

```
cups_install: True
cups_enabled: True
```

Visit your IIAB's http://box/print > **Administration** and log in using:

- Username: `Admin`
- Password: `changeme`

Or use any Linux account that is a member of the Linux group: `lpadmin`

_Browser pop-ups will try to scare you &mdash; click (and persist!) to log in despite these exaggerated warnings._

## Security

The above uses 'SystemGroup lpadmin' in `/etc/cups/cups-files.conf` &mdash; in coordination with about 15 '@SYSTEM' lines and 'DefaultAuthType Basic' in `/etc/cups/cupsd.conf`

CUPS creates a 10-year (unsigned) HTTPS certificate during installation, that will be very confusing to non-technical users when they log in, as a result of modern browser warnings.

## How it Works

Understand how IIAB configures CUPS for all IP addresses and all hostnames (IIAB redirects to bypass the "since 2009" CUPS problem mentioned below!) by reading these in-line explanations:

- [/opt/iiab/iiab/roles/cups/tasks/install.yml](tasks/install.yml)

Modify these 2 files at your own risk:

- [/etc/cups/cupsd.conf](https://www.cups.org/doc/man-cupsd.conf.html) (run `sudo cupsctl` and `sudo cupsd -t` to verify the file!)
- [/etc/nginx/conf.d/cups.conf](templates/cups.conf.j2)

If you make modifications to the above files, don't forget to restart systemd services: (run this as root)

```
systemctl restart cups cups-browsed nginx
```

## Troubleshooting

Visit your IIAB's http://box/print > **Help** for printer configuration suggestions, Etc!

http://localhost:631 is very useful if NGINX redirects or CUPS permissions are set wrong.

Beware that http://box:631 and http://box.lan:631 _will not work,_ due to a [known issue](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=530027) with CUPS since 2009.

Run `ps aux | grep cups` and `systemctl status cups` to verify the CUPS systemd service is running well.

Finally, keep an eye on: `/var/log/cups/error_log`

## Docs and Updates

- https://www.cups.org/documentation.html
  - https://github.com/apple/cups/releases
- https://openprinting.github.io/cups/
  - https://github.com/OpenPrinting/cups/releases/
