09-clone goes in scripts
11-set-freq goes in scripts
50-hostapd goes in /lib/dhcpcd/dhcpcd-hooks/
wpa_supplicant-uap0.conf /etc/wpa_supplicant/
wpa_supplicant@.service goes in /etc/systemd/system 
systemctl enable wpa_supplicant@.service

11-set-freq needs to have a fallback should wlan0 not in use as upstream
wlan0-timer needs to be called from /etc/rc.local or setup a unit file firing after dhcpcd
