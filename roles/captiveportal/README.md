_Please Also See: http://FAQ.IIAB.IO > ["Captive Portal Administration: What tips & tricks exist?"](https://wiki.iiab.io/go/FAQ#Captive_Portal_Administration:_What_tips_&_tricks_exist%3F)_

## Theory of Operation

* The captive portal function is a feature of most modern operating systems. With the increased use of https/ssl (secure sockets layer), the automatic diversion to a specific web page runs the risk of being detected as a "man in the middle" attack.
* Each Operating System (OS) provides a mechanism that IIAB can use to break into a conversation, when SSL is not being used. This is an initial attempt by the OS to talk to one of its own web sites, to determine if the host os is connected to the internet. It is always performed without SSL.
* The IIAB captive portal uses a list of these OS supported web sites, and diverts these requests to the IIAB server, which in turn forwards to the IIAB home page.
* While the portal is active -- `captiveportal_enabled: True`, a LAN interface is present, and `iiab_gateway_enabled` is not True (i.e. IIAB is not providing Internet to client devices) -- probe hostnames resolve to `198.51.100.1` by default (`captiveportal_probe_ip`), an unroutable TEST-NET-2 address reserved by RFC 5737. External LAN TCP port 80 traffic is redirected to the IIAB server, including devices such as Samsung clients that resolve probes using their own DNS; destinations within the configured LAN subnet are excluded so local HTTP services remain reachable. `iiab-make-cp-servers.py` (dnsmasq) and `iiab-gen-iptables` (firewall) apply the same condition, so the DNS diversion and the port-80 redirect always switch together.
* The normal IIAB NGINX server explicitly handles the configured LAN IP and local aliases (`box.lan` and `box.local`) before the portal's default server. This preserves the captive portal for unmatched probe traffic while allowing `http://<lan-ip>/` and mDNS clients to reach IIAB without resolving the canonical FQDN. `box.lan` is IIAB's canonical DNS name; `box.local` is also accepted as an mDNS/Avahi alias when clients support it.

## Components of the IIAB Captive Portal

* Files used
    1. checkurls -- the list of urls use by at least one of the OS's.
    1. iiab-make-cp-servers.py -- Python script writes the nginx configuration file to /etc/nginx/sites-available and creates or removes the matching dnsmasq diversion
    1. capture-wsgi.py -- determines the client agent, stores short-lived client state in memory, and responds with redirects as appropriate for each OS.
    1. captiveportal.ini.j2 -- config file for the `uwsgi-app@captiveportal.service` instance, which runs the capture-wsgi.py script.
    1. `uwsgi-app@captiveportal.service` and `uwsgi-app@captiveportal.socket` -- the distro-provided per-application systemd units for the Captive Portal.
    
### uWSGI service and socket

The `uwsgi-app@captiveportal.service` instance uses the instance name
`captiveportal` to load `/etc/uwsgi/apps-available/captiveportal.ini`.
The matching socket unit listens on
`/run/uwsgi/captiveportal.socket`, and NGINX's generated Captive Portal
configuration uses the native uWSGI protocol over that socket.

The Captive Portal service uses the distro-provided uWSGI unit; IIAB does not
override that unit's service user or hardening settings. The application
writes its logs to stderr, which systemd captures in the journal. Service
startup and application errors can be inspected with:

    sudo journalctl -u uwsgi-app@captiveportal.service

The service stores client state in memory only. Entries expire after one hour
without a request and all state is lost when the Captive Portal service
restarts; no client-state database is used. The 30-second inactivity threshold
applies to incomplete portal flows.

When running `capture-wsgi.py` directly for debugging, it listens on TCP
port `9090` by default. Override the port with `--port`, or set
`CAPTIVE_PORTAL_PORT`; the command-line flag takes precedence. The systemd
service does not use TCP.

Set `captiveportal_log_probes: True` to log each probe URL received by the
portal at INFO level. The log entry includes the probe host, path, and query
string and is written to the uWSGI service journal:

    sudo journalctl -u uwsgi-app@captiveportal.service

When the captive portal is active, the same setting also logs external LAN HTTP
requests before redirection to the portal. These kernel firewall
messages use the `WWW-ATTEMPT:` prefix and can be viewed with:

    sudo dmesg | grep 'WWW-ATTEMPT:'

Windows/NCSI desktop probe requests redirect directly to the configured IIAB
homepage. macOS/iOS sign-in assistants and Android clients first receive a
captive-portal instruction page. It explains how to dismiss the OS sign-in
window and open the configured FQDN (such as `http://box.lan`) in a regular
browser. macOS/iOS and supported Android offer **"Use Without Internet"** in
the three-dots menu; choosing it dismisses the sign-in window without opening
the IIAB page, so the splash shows that wording in red as a caution. The
splash also lists two manual addresses --
`http://box.lan` and `http://box` -- as large text that can be tapped to copy;
while the portal is active both resolve to the IIAB server (see
`iiab-make-cp-servers.py`), which matters for clients that cannot resolve the
FQDN by mDNS (`box.local` is also offered by mDNS/Avahi when the client
supports it). The page's button records the portal completion event and opens
the configured IIAB homepage; web pages cannot reliably close the operating
system's sign-in window themselves.

If macOS Safari does not surface a sign-in window, it handles
`captive.apple.com` silently even when the URL is typed by hand, so a macOS
user should open `http://box.local` (mDNS) or `http://box` directly in a
regular browser. GNOME's portal check fetches
`http://fedoraproject.org/static/hotspot.txt`, which the portal handles like
the other portal probes rather than redirecting to homepage HTML that can
leave the embedded browser tab hanging.

### Curl integration test

Run the captive-portal integration test on the IIAB host while the portal is
enabled:

    bash roles/captiveportal/tests/captiveportal-curl.sh

The test sends requests through the local NGINX listener and uses different
loopback source addresses for each simulated client, so the portal's
in-memory client state does not leak between cases. The defaults assume the
canonical IIAB host is `box.lan`; override `CAPTIVE_PORTAL_TEST_HOME_URL` and
the other `CAPTIVE_PORTAL_TEST_*` variables when testing a different
configuration.

For a client with a completed portal session, every recognized connectivity
probe receives the success answer its operating system expects while probe
traffic continues, rather than a redirect back to the splash page:

* Android/Chromium (`generate_204`, `clients3.google.com`, gstatic, MIUI,
  Huawei/Honor, Samsung): `204 No Content`.
* Firefox (`detectportal.firefox.com/success.txt`): the literal body `success`.
* Windows NCSI (`www.msftconnecttest.com/connecttest.txt`): the literal body
  `Microsoft Connect Test`.
* iOS/macOS (Apple hosts): the classic `Success` page, or the bare word
  `Success` for `/library/test/success.html`.

This suppresses repeated sign-in prompts *and* any "Limited connection" /
"No internet access" verdict during the active connection. Completion expires
after one hour without a request, and the following request starts another
portal session. A probe under an unknown hostname (e.g. an unrecognized OEM
fork, or a client resolving probes with its own DNS) also receives
`204 No Content` when the portal session is complete, as long as its path looks
like a probe. Some Android versions additionally perform HTTPS validation,
which requires a trusted certificate and is not intercepted by IIAB.

If the portal backend is unavailable, its nginx server answers probe requests
with a `302` to the IIAB homepage rather than a `502`, so a stopped or wedged
uWSGI instance does not read to clients as "no Internet".

For direct runs, use `--log-probes` (or `--log-urls`) or set
`CAPTIVE_PORTAL_LOG_PROBES=1`. The existing `--log-file` option can be used to
write these entries to a rotating file.

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
 * Run `capture-wsgi.py -v --port 9090` in a terminal for debug-level logging.
   You can alternatively set `CAPTIVE_PORTAL_PORT=9090`. To also
   write a rotating file log during direct debugging, pass
   `--log-file /tmp/captiveportal.log` or set
   `CAPTIVE_PORTAL_LOG_FILE=/tmp/captiveportal.log`.
 * To discover untrapped urls, "apt-get install tcpdump", and "tcpdump -i br0 capture.tcp". I transfer this file to a machine with a GUI, and wireshark to interpret the conversations on the wire. The DNS packets are the ones to look for.
 
 ## Known Problems
 1. On Android 5-7, the browser which is brought up, during the association process, is a 'walled garden' and I cannot find a way out. This browser is not very modern, and continuously displays the "sign in to Wi-Fi network" button -- with an annoying beep.
