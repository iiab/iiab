#### How to Do a Headless Wifi Install to a Raspberry Pi 

* Download the raspbian image
* Copy it to an SD card
* Touch /boot/ssh on the first partition on your newly imaged SD card
* Power on the rpi, and attach an ethernet cable from your laptop to the
* Ping raspberrypi.local to verify that you can communicate to the device
* Ssh into the pi with username pi, and password raspberry
```
   ssh pi@raspberrypi.local
```
* Use nano or vi to add the following to bottom of /etc/wpa_supplicant/wpa_supplicant.conf
```
network={
    ssid=<YOUR SSID>
    psk=<SSID PASSWORD>
}
```
* Reboot, log in again, and use "ip a" to verify that the wlan0 has an inet address
* Get the online script to load IIAB onto your rpi

```
wget http://download.iiab.io/6.4/rpi/load-lite.txt
```
* Look at the downloaded script, and verify that it is what you want
* Do the install
```
  cat load-lite.txt | sudo bash
```
* After the script completes you can add content
* And/or make the Wifi into a stand alone hotspot (or gateway if you add an internet connected ethernet wire) 
```
  hotspot (this script is not yet available; but will be before release of 6.4)
```
* now you must asociate to the wifi with the default SSID "internet in a box" 
