==============
Gateway README
==============

Under the heading of Gateway are a number of services that provide dhcp addresses and NAT to the lan 
and filter wan access both in terms of content and bandwidth.

LAN
---

The LAN is managed by the dhcpd service and by iptables.  The configuration of iptables is complicated
and works as follows:

/etc/systemd/system/iptables.service calls 
/etc/sysconfig/iptables-config which calls 
/usr/bin/xs-gen-iptables
and saves the resultant configuration to /etc/sysconfig/iptables
it then supplies additional rules to iptables

As of March 2014 the following files are obsolete

/etc/sysconfig/olpc-scripts/iptables-xs 

/etc/sysconfig/olpc-scripts/ip6tables-xs

Filters
-------

Content is filtered by squid and dansguardian and there are ansible variables that control them.

There is a white list file, sites.whitelist.txt.  URL patterns not in this file will not be accessible.

An additional rule to block https has been added to iptables, also controlled by an ansible variable.

**N.B. https blocking and whitelist checking are disabled by default**

To enable whitelist checking and/or https blocking edit 

#Gateway Filters
gw_squid_whitelist: False
gw_block_https: False

changing False to True where appropriate and then run runtags facts, gateway 

Bandwidth is filtered by wondershaper.

