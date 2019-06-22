## Objective

To streamline troubleshooting of remote Internet-in-a-Box (IIAB) installations, we bundle up common machine/software diagnostics, all together in 1 human-readable file, that can be easily circulated online AND offline.

The ``pastebinit`` command can then be used to upload this file, creating a short URL that makes things even easier.

But first off, the file is compiled by harvesting 4 kinds of things:

1. Files
   1. /etc/iiab/iiab.env
   2. /etc/iiab/iiab.ini
   3. /etc/iiab/local_vars.yml
   4. /etc/iiab/config_vars.yml
   5. /etc/iiab/openvpn_handle
   6. /etc/resolv.conf
   7. /etc/network/interfaces
   8. /usr/bin/iiab-gen-iptables
   9. /.iiab-image

2. Contents of Directories:
   1. /etc/network/interfaces.d
   2. /etc/sysconfig/network-scripts/if-cfg*
   3. /etc/NetworkManager/system-connections
   4. /etc/systemd/network/

3. Output from Commands:
   1. ip addr    # Network interfaces
   2. ifconfig    # Network interfaces (old view)
   3. brctl show    # Bridge for LAN side
   4. netstat -rn    # Routing table
   5. netstat -natp    # Ports/Services in use
   6. iptables-save    # Firewall rules
   7. systemctl status dnsmasq    # Is dnsmasq Ok?
   8. journalctl -u dnsmasq    # dnsmasq log
   9. ansible localhost -m setup 2>/dev/null    # All Ansible facts

4. Log Files -- last 100 lines:
   1. /opt/iiab/iiab-install.log
   2. /opt/iiab/iiab-network.log
   3. /opt/iiab/iiab-debug.log
   4. /opt/iiab/iiab-admin-console/admin-install.log

#### Suggested Usage 

1. Run the diagnostics:

   ```
   sudo iiab-diagnostics
   ```

   ( This will bundle up all the diagnostics, into a new file places in: /etc/iiab/diagnostics/ )

2. Upload the file using the pastebinit command:

   ```
   pastebinit < /etc/iiab/diagnostics/<name of file you just created>
   ```
   
   This will generalte a link (URL).

3. Post the link (URL) to a "New issue" at https://github.com/iiab/iiab/issues

   Include a description of the symptoms, and how to reproduce the problem.

4. If you don't understand Step 3, email everything to bugs@iiab.io instead.
