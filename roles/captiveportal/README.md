_Please Also See: http://FAQ.IIAB.IO > ["Captive Portal Administration: What tips & tricks exist?"](https://wiki.iiab.io/go/FAQ#Captive_Portal_Administration:_What_tips_&_tricks_exist%3F)_

## Theory of Operation

* The captive portal function is a feature of most modern operating systems. With the increased use of https/ssl (secure sockets layer), the automatic diversion to a specific web page runs the risk of being detected as a "man in the middle" attack.
* Each Operating System (OS) provides a mechanism that IIAB can use to break into a conversation, when SSL is not being used. This is an initial attempt by the OS to talk to one of its own web sites, to determine if the host os is connected to the internet. It is always performed without SSL.
* The IIAB captive portal uses a list of these OS supported web sites, and diverts these requests to the IIAB server, which in turn forwards to the IIAB home page.

## Components of the IIAB Captive Portal

* Files used
    1. checkurls -- the list of urls use by at least one of the OS's.
    1. iiab-divert-to-nginx -- Bash script writes dnsmasq config file which points to IIAB server
    1. iiab-make-cp-servers.py -- Python script writes nginx configuration file to /etc/nginx/sites-enabled
    1. capture-wsgi.py -- the script which determines the client agent, records it in sqlite database, and responds with redirects as appropriate for each OS.
    1. captiveportal.ini.j2 -- config file for the `uwsgi-app@captiveportal.service` instance, which runs the capture-wsgi.py script.
    1. `uwsgi-app@captiveportal.service` and `uwsgi-app@captiveportal.socket` -- the distro-provided per-application systemd units for the Captive Portal.
    
### uWSGI service and socket

The `uwsgi-app@captiveportal.service` instance uses the instance name
`captiveportal` to load `/etc/uwsgi/apps-available/captiveportal.ini`.
The matching socket unit listens on
`/run/uwsgi/captiveportal.socket`, and NGINX's generated Captive Portal
configuration uses the native uWSGI protocol over that socket.

The Captive Portal service uses the distro uWSGI unit's `DynamicUser=yes`
hardening and writes its application logs to stderr, which systemd captures
in the journal. Service startup and application errors can be inspected with:

    sudo journalctl -u uwsgi-app@captiveportal.service

The service stores its client-state database as `users.sqlite` in the
systemd-provided `STATE_DIRECTORY` (the distro unit declares
`StateDirectory=uwsgi/%i`). Direct runs use
`/opt/iiab/captiveportal/users.sqlite` as a fallback.

The `captiveportal_port` variable is retained only for running
`capture-wsgi.py` directly for debugging; it is not used by the systemd
service.

The Admin Console is a separate socket-activated uWSGI instance,
`uwsgi-app@admin-console.service`, and listens on the Unix socket
`/run/uwsgi/admin-console.socket`. Neither uWSGI instance uses TCP port
`9090`; port `9091` is the Transmission web interface and is unrelated to
either uWSGI instance.

 ## Extending and Debugging Captive Portal
 * Running the capture-wsgi.py python script interactively will expose any python errors easily. 
 * The Python capture script can be run interactively instead of automatically by uWSGI. Stop the Captive Portal socket and service first:
   `sudo systemctl stop uwsgi-app@captiveportal.socket uwsgi-app@captiveportal.service`
   Stopping this instance does not stop the Admin Console instance.
 * Run `capture-wsgi.py -v` in a terminal for debug-level logging. To also
   write a rotating file log during direct debugging, pass
   `--log-file /tmp/captiveportal.log` or set
   `CAPTIVE_PORTAL_LOG_FILE=/tmp/captiveportal.log`.
 * To discover untrapped urls, "apt-get install tcpdump", and "tcpdump -i br0 capture.tcp". I transfer this file to a machine with a GUI, and wireshark to interpret the conversations on the wire. The DNS packets are the ones to look for.
 
 ## Known Problems
 1. On Android 5-7, the browser which is brought up, during the association process, is a 'walled garden' and I cannot find a way out. This browser is not very modern, and continuously displays the "sign in to Wi-Fi network" button -- with an annoying beep.
