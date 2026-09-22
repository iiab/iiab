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
    1. `uwsgi-app@captiveportal.service` -- the distro-provided per-application systemd unit for the Captive Portal.
    
### uWSGI service and port mapping

The service name does not assign a port. The `uwsgi-app@captiveportal.service`
instance uses the instance name `captiveportal` to load
`/etc/uwsgi/apps-available/captiveportal.ini`. That INI sets
`http-socket = :<captiveportal_port>`, which defaults to port `9090`.
NGINX's generated Captive Portal configuration proxies to the same port.

The Admin Console is a separate uWSGI instance,
`uwsgi-app@admin-console.service`, and listens on the Unix socket
`/tmp/admin-console.sock`; it does not use port `9090`. Port `9091` is the
Transmission web interface and is unrelated to either uWSGI instance.

 ## Extending and Debugging Captive Portal
 * Running the capture-wsgi.py python script interactively will expose any python errors easily. 
 * The Python capture script can be run interactively instead of automatically by uWSGI. Stop the Captive Portal instance first to free its configured port (`9090` by default):
   `sudo systemctl stop uwsgi-app@captiveportal.service`
   Two programs cannot listen on the same port. Stopping this instance does not stop the Admin Console instance; restart it afterward with `sudo systemctl start uwsgi-app@captiveportal.service`.
 * Run the capture-wsgi.py with "-l" in a terminal to increase logging to /var/log/captiveportal/captiveportal.log
 * To discover untrapped urls, "apt-get install tcpdump", and "tcpdump -i br0 capture.tcp". I transfer this file to a machine with a GUI, and wireshark to interpret the conversations on the wire. The DNS packets are the ones to look for.
 
 ## Known Problems
 1. On Android 5-7, the browser which is brought up, during the association process, is a 'walled garden' and I cannot find a way out. This browser is not very modern, and continuously displays the "sign in to Wi-Fi network" button -- with an annoying beep.
