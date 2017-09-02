#### How to Install from Scratch to a Raspberry Pi via Wifi Without keyboard or Monitor

* Download the raspbian image
* Copy it to an SD card
* Touch /boot/ssh on the first partition on your newly imaged SD card
* Power on the rpi, and attach an ethernet cable from your laptop to the
* Ping raspberrypi.local to verify that you can communicate to the device
* Ssh into the pi with username pi, and password raspberry
* Use nano or vi to add the following to bottom of /etc/wpa_supplicant/wpa_supplicant.conf
```
network={
    ssid=<YOUR SSID>
    psk=<SSID PASSWORD>
}
```
* Reboot, log in again, and use "ip a" to verify that the wlan0 has an inet address
* Run the online script to load IIAB onto your rpi

```
wget http://download.iiab.io/6.4/rpi/load-lite.txt
```
* Look downloaded script, verify that it is what you want
* Do the install
```
  cat load-lite.txt | sudo bash
```
