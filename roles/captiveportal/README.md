_Please Also See: http://FAQ.IIAB.IO > ["Captive Portal Administration: What tips & tricks exist?"](http://wiki.laptop.org/go/IIAB/FAQ#Captive_Portal_Administration:_What_tips_.26_tricks_exist.3F)_

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
    1. captiveportal.ini.j2 -- config file for uwsgi service, which in turn runs the capture-wsgi.py script.
    1. uwsgi.service -- systemd unit file which runs python3 programs --permits captive portal and admin-console python scripts to function.
    
 ## Extending and Debugging Captive Portal
 * Running the capture-wsgi.py python script interactively will expose any python errors easily. 
 * The python capture script can be run interactively in terminal rather than automatically by uwsgi -- (use "systemctl stop uwsgi" to free up the port used by captive portal: 9090). The uwsgi service for captive portal grabs port 9090, and two programs cannot share the same port. NOTE: that while the uwsgi service is stopped, the admin-console will not function).
 * Run the capture-wsgi.py with "-l" in a terminal to increase logging to /var/log/captiveportal/captiveportal.log
 * To discover untrapped urls, "apt-get install tcpdump", and "tcpdump -i br0 capture.tcp". I transfer this file to a machine with a GUI, and wireshark to interpret the conversations on the wire. The DNS packets are the ones to look for.
 
 ## Known Problems
 1. On Android 5-7, the browser which is brought up, during the association process, is a 'walled garden' and I cannot find a way out. This browser is not very modern, and continuously displays the "sign in to Wi-Fi network" button -- with an annoying beep.
