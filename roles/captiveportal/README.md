_Please Also See: http://FAQ.IIAB.IO > ["Captive Portal Administration: What tips & tricks exist?"](https://wiki.iiab.io/go/FAQ#Captive_Portal_Administration:_What_tips_&_tricks_exist%3F)_

## Theory of Operation

* The captive portal function is a feature of most modern operating systems. With the increased use of https/ssl (secure sockets layer), the automatic diversion to a specific web page runs the risk of being detected as a "man in the middle" attack.
* Each Operating System (OS) provides a mechanism that IIAB can use to break into a conversation, when SSL is not being used. This is an initial attempt by the OS to talk to one of its own web sites, to determine if the host os is connected to the internet. It is always performed without SSL.
* The IIAB captive portal uses a list of these OS supported web sites, and diverts these requests to the IIAB server, which in turn forwards to the IIAB home page.
* While the portal is active -- `captiveportal_enabled: True`, a LAN interface is present, and `iiab_gateway_enabled` is not True (i.e. IIAB is not providing Internet to client devices) -- probe hostnames resolve to `198.51.100.1` by default (`captiveportal_probe_ip`), an unroutable TEST-NET-2 address reserved by RFC 5737. External LAN TCP port 80 traffic is redirected to the IIAB server, including traffic from devices such as Samsung clients that resolve probes using their own DNS; destinations within the configured LAN subnet are excluded so local HTTP services remain reachable. The role renders `capture-dnsmasq.j2` to `/etc/iiab/captiveportal-dnsmasq`, and `iiab-gen-iptables` copies it to `/etc/dnsmasq.d/capture` (and removes it again) under the same condition as the port-80 redirect, so the DNS diversion and the redirect always change together.
* Other hostnames fall back to the IIAB LAN address while the portal is active, so URLs such as `http://a` and unrecognized OEM probes also reach the portal. Names in `/etc/hosts.dnsmasq` or DHCP leases keep their real addresses, `localhost` stays on `127.0.0.1`, and names in the configured IIAB domain (`.lan` by default) are resolved locally only. The fallback is removed with the rest of the generated dnsmasq fragment when the portal is inactive.
* The normal IIAB NGINX server explicitly handles the configured LAN IP, any IPv4 address literal (including the host's WAN address and loopback), and local aliases (`box.lan` and `box.local`) before the portal's default server. This preserves the captive portal for unmatched probe traffic while allowing `http://<lan-ip>/`, `http://<wan-ip>/`, and mDNS clients to reach IIAB without resolving the canonical FQDN. `box.lan` is IIAB's canonical DNS name; `box.local` is offered by mDNS/Avahi, and the portal's dnsmasq catch-all also resolves it while the portal is active.

## Components of the IIAB Captive Portal

* Files used
    1. checkurls -- the source list of URLs used by at least one operating system.
    1. capture.conf.j2 -- the NGINX default server for unmatched probe requests.
    1. capture-dnsmasq.j2 -- the dnsmasq diversion rendered from the checkurls list to `/etc/iiab/captiveportal-dnsmasq` and activated as `/etc/dnsmasq.d/capture` by `iiab-gen-iptables`.
    1. capture-wsgi.py -- determines the client agent, stores short-lived client state in memory, and responds with redirects as appropriate for each OS.
    1. captiveportal.ini.j2 -- configuration file for the `uwsgi-app@captiveportal.service` instance, which runs the capture-wsgi.py script.
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

The service stores client state in memory only. Entries expire after 15 minutes
without a request, and all state is lost when the Captive Portal service
restarts; no client-state database is used. The splash display timer (eight
seconds) starts only when the shared splash page is served. A separate
unconditional timer completes the client twelve seconds after its first request,
so clients that never open the splash page are still allowed through.

When running `capture-wsgi.py` directly for debugging, it listens on TCP
port `9090` by default. Override the port with `--port`, or set
`CAPTIVE_PORTAL_PORT`; the command-line flag takes precedence. The systemd
service does not use TCP.

Set `captiveportal_log_probes: True` to log each probe URL received by the
portal at the INFO level. Each entry includes the probe host, path, and query
string, and is written to the uWSGI service journal:

    sudo journalctl -u uwsgi-app@captiveportal.service

When the captive portal is active, the same setting also logs external LAN HTTP
requests before redirection to the portal. These kernel firewall
messages use the `WWW-ATTEMPT:` prefix and can be viewed with:

    sudo dmesg | grep 'WWW-ATTEMPT:'

RFC 8910 Captive Portal API discovery is not advertised: DHCP option 114
requires an HTTPS URL with a certificate the client trusts, and IIAB does not
provide one for this portal. Portal discovery therefore relies on the legacy
HTTP probes.

macOS/iOS and Android clients see a single shared informational splash page,
matching Nodogsplash's pre-authentication flow. Desktop probes, including
Windows/NCSI, Firefox, and Linux desktop checks, first redirect to that same
splash and then redirect to the configured IIAB homepage after the grace
period. The page explains that the network provides offline access. It lists
manual IIAB addresses -- `http://box.lan` and `http://box.local` -- as large
text that can be selected or tapped to copy. While the portal is active, both resolve to
the IIAB server (see `capture-dnsmasq.j2`). This helps clients that cannot
resolve the FQDN through mDNS (`box.local` is also advertised by mDNS/Avahi
when the client supports it). The shared splash refreshes after eight seconds
for desktop clients so the Captive Portal backend can return the final `302`
to the IIAB homepage. Desktop Apple clients may close the window; mobile
clients may close the page. After the splash page has been shown for eight
seconds, every client completes automatically, even if the page was closed
first; clients that never open the splash page are completed twelve seconds
after their first request. Apple clients receive Apple's `Success` response on
their next connectivity probe, while Android clients receive the no-content
response expected by their connectivity check. As in Nodogsplash, repeating a
pre-authentication request keeps that client in the splash flow, while
completion changes only that client's subsequent probe responses. Web pages
cannot reliably close the operating system's sign-in window.

macOS Safari handles `captive.apple.com` silently even when the URL is typed
by hand, and may therefore not surface a sign-in window. A macOS user should
open `http://box.local` (mDNS) or `http://box` directly in a regular browser.
GNOME's portal check fetches `http://fedoraproject.org/static/hotspot.txt`,
which the portal treats like the other probes instead of returning homepage
HTML that can leave the embedded browser tab hanging.

### Curl integration test

Run the captive-portal integration test on the IIAB host while the portal is
enabled:

    bash roles/captiveportal/tests/captiveportal-curl.sh

The test sends requests through the local NGINX listener and uses different
loopback source addresses for each simulated client, so the portal's
in-memory client state does not leak between cases. The defaults assume the
canonical IIAB host is `box.lan`; override `CAPTIVE_PORTAL_TEST_HOME_URL` and
the other `CAPTIVE_PORTAL_TEST_*` variables when testing a different
configuration. `CAPTIVE_PORTAL_TEST_LOCAL_IP` (default: the host's first
address from `hostname -I`, or `127.0.0.1`) verifies that requesting IIAB by
one of the host's own addresses reaches the normal homepage instead of the
Captive Portal default_server.

For a client with a completed portal session, every recognized connectivity
probe receives the success answer its operating system expects, rather than a
redirect back to the splash page:

* Chromium-family browsers (Chrome, Edge, Opera) and their Google/Edge
  `generate_204` endpoints: `204 No Content`.
* Android vendor probes (`generate_204`, MIUI, Huawei/Honor, Samsung):
  `204 No Content`.
* Firefox (`detectportal.firefox.com/success.txt`): the literal body `success`.
* Linux desktop checks: Ubuntu and openSUSE receive `204 No Content`;
  Fedora and KDE receive `OK`; GNOME NetworkManager receives
  `NetworkManager is online`.
* Windows NCSI (`www.msftncsi.com/ncsi.txt`): the literal body `Microsoft NCSI`;
  Windows Connect Test (`www.msftconnecttest.com/connecttest.txt`): the literal
  body `Microsoft Connect Test`.
* iOS/macOS (Apple hosts): the classic HTML `Success` page.

This prevents repeated sign-in prompts and any "Limited connection" or
"No internet access" warning while the connection is active. The completed
state expires after 15 minutes without a request, and the next request starts a
new portal session. A probe under an unknown hostname (e.g. an unrecognized
OEM fork, or a client resolving probes with its own DNS) also receives
`204 No Content` when the portal session is complete, as long as its path looks
like a probe. Some Android versions additionally perform HTTPS validation,
which requires a trusted certificate and is not intercepted by IIAB.
In offline mode, forwarded external HTTPS connections are rejected promptly
with a TCP reset; local IIAB HTTPS services remain reachable. The portal
continues to intercept only HTTP connectivity probes.

If the portal backend is unavailable, its NGINX server answers probe requests
with a `302` to the IIAB homepage rather than a `502`, so a stopped or wedged
uWSGI instance does not appear to clients as "no Internet".

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
  1. Some Android versions perform an HTTPS connectivity check after the
     captive portal flow. IIAB does not intercept HTTPS, so that check requires
     a trusted certificate and may continue to report limited connectivity even
     after the HTTP portal session completes.
