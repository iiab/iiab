#! /bin/bash
echo -e "removing /etc/NetworkManager/conf.d/IIAB-Slave-*.conf \n"
rm /etc/NetworkManager/conf.d/IIAB-Slave-*.conf
echo -e "removing /etc/systemd/network/IIAB-Slave-*.network \n"
rm /etc/systemd/network/IIAB-Slave-*.network
echo -e "reboot to deactivate slaves devices. \n"
