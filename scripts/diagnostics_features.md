## Objective 
* Creates a flat file which can be uploaded to pastebinit. Gathers the following:

1. /etc/iiab/iiab.ini
2. /etc/iiab/iiab.env
3. Output of /sbin/ip addr command
4. Output of /sbin/ifconfig command
5. Output of /sbin/brctl show
6. /etc/resolv.conf
7. Output of /bin/netstat -rn (routing table)
8. Output from /bin/netstat -natp (which services have which ports)
9. /opt/iiab/iiab-install.log
10. /opt/iiab/iiab-debug.log
11. /opt/iiab-network.log
12. all ansible facts

contents of following directories:

1. /etc/network/interfaces.d (and interfaces)
2. /etc/sysconfig/network-scripts/if-cfg*
3. /etc/NetworkManager/system-connections
4. /etc/systemd/network/

#### Suggested Usage 
1. Create a diagnostic package
```
sudo iiab-diagnostics
```
(this will generate a new file with the collected information and place it into /etc/iiab/diagnostics/)

2. Upload the diagnostics you have just generated to pastebinit.
```
 pastebinit -i /etc/iiab/diagnostics/<name of file you just created>
```
3. Email a description of the symptoms, and how to generate them, along with the URL which was returned by the "pastebinit" command, to bugs@iiab.io.
