#### Objective ####
* Creates a tgz which includes  user's name, date, operating system in title. Creates tgz less than 1MB. Can be read by vi without untaring.Gathers the following:

1. iiab.ini
2. iiab.env
3. ip addr
4. ifconfig
5. brctl show
6. /etc/resolv.conf
7. netstat -rn (routing table)
8. netstat -natp (which services have which ports)
9. iiab-install.log
10. iiab-debug.log
11. iiab-network.log
12. all ansible variables

contents of following directories:

1. /etc/network/interfaces.d (and interfaces)
2. /etc/sysconfig/network-scripts/if-cfg*
3. /etc/NetworkManager/system-connections
4. /etc/systemd/network/

#### Suggested Usage ####
1. Upload the diagnostics you have just generated to pastebinit.
```
pbput /etc/iiab/diagnostics/<diagnostics file name>
```
2. Email a description of the symptoms, and how to generate them, along with the URL which was returned by the "pbput" command, to bugs@iiab.io.
