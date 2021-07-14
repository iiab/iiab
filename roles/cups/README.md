# CUPS Printing README

## Web Administration

Please administer CUPS at http://box/print using:

- Username: `Admin`
- Password: `changeme`

Or use any Linux user that is a member of the Linux group: `lpadmin`

## Security

The above uses 'SystemGroup lpadmin' in `/etc/cups/cups-files.conf` &mdash; in coordination with about 15 '@SYSTEM' lines and 'DefaultAuthType Basic' in `/etc/cups/cupsd.conf`

CUPS creates a 10-year (unsigned) https certificate during installation, that will be very confusing to non-technical users when they log in, as a result of modern browser warnings.

## How it Works

http://localhost:631 can be useful if NGINX redirects or CUPS permissions are set wrong.

Beware that http://box:631 and http://box.lan:631 will not work, due to a [known issue](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=530027) with CUPS since 2009.

Understand how IIAB configures CUPS for all IP addresses and all hostnames (despite the above CUPS problem!) by reading these in-line explanations:

- [/opt/iiab/iiab/roles/cups/tasks/install.yml](tasks/install.yml)

Modify these 2 files at your own risk:

- [/etc/cups/cupsd.conf](https://www.cups.org/doc/man-cupsd.conf.html) (run `sudo cupsctl` and `sudo cupsd -t` to verify the file!)
- [/etc/nginx/conf.d/cups.conf](templates/cups.conf.j2)

If you make modifications to the above files, don't forget to restart systemd services:

```
systemctl restart cups cups-browsed nginx
```

## Docs and Updates

- https://www.cups.org/documentation.html
  - https://github.com/apple/cups/releases
- https://openprinting.github.io/cups/
  - https://github.com/OpenPrinting/cups/releases/
