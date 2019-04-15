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
1. Use a FAT formatted USB stick (FAT format is recognized by both Windows and Mac) to move /etc/iiab/footprint/<footprint.tgz> to a machine that has internet access and a browser.
2. Upload the footprint to  https://filebin.ca, record the returned URL, and email that URL, along with a description of the symptoms, to xsce-devel@googlegroups.com.
