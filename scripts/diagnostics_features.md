## Objective 

Create a flat file which can be uploaded to pastebinit.

File contains 4 kinds of things:

1. Files
   1. /etc/iiab/iiab.ini
   2. /etc/iiab/iiab.env
   3. /etc/iiab/local_vars.yml
   4. /etc/iiab/config_vars.yml
   5. /etc/resolv.conf
   6. /opt/iiab/iiab-install.log
   7. /opt/iiab/iiab-debug.log
   8. /opt/iiab/iiab-network.log

2. Facts:
   1. All Ansible facts

3. Output from commands:
   1. Output of /sbin/ip addr
   2. Output of /sbin/ifconfig
   3. Output of /sbin/brctl show
   4. Output of /bin/netstat -rn (routing table)
   5. Output of /bin/netstat -natp (which services have which ports)
   ...
   systemctl status dnsmasq
   journalctl -u dnsmasq

4. as well as contents of following directories:
   1. /etc/network/interfaces.d (and interfaces)
   2. /etc/sysconfig/network-scripts/if-cfg*
   3. /etc/NetworkManager/system-connections
   4. /etc/systemd/network/

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
