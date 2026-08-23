## Install

1. Install [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. Click a `.rpi-imager-manifest` link in the "Assets" section below.

<details>
<summary><h3>CLICK HERE for Raspberry Pi Imager instructions</h3></summary>

1. Click a `.rpi-imager-manifest` link under "Assets", then double-click the downloaded file to open it in Raspberry Pi Imager. If nothing happens, right-click the file and choose "Open With: Raspberry Pi Imager".

<img width="746" height="143" alt="Image" src="https://raw.githubusercontent.com/iiab/iiab/master/.github/assets/rpi-imager-step1-open-manifest.png" />

2. Select any device to continue.

<img width="675" height="477" alt="Image" src="https://raw.githubusercontent.com/iiab/iiab/master/.github/assets/rpi-imager-step2-select-device.png" />

3. Select Internet in a Box as the operating system.

<img width="678" height="480" alt="Image" src="https://raw.githubusercontent.com/iiab/iiab/master/.github/assets/rpi-imager-step3-select-os.png" />

4. Select the storage media to write to. Raspberry Pi Imager only lists removable drives, but double-check before continuing -- this erases everything on the selected drive.

<img width="677" height="474" alt="Image" src="https://raw.githubusercontent.com/iiab/iiab/master/.github/assets/rpi-imager-step4-select-storage.png" />

5. Set the hostname to `box`.

<img width="670" height="471" alt="Image" src="https://raw.githubusercontent.com/iiab/iiab/master/.github/assets/rpi-imager-step5-customise.png" />

6. Continue through the wizard with `NEXT`; do not click `SKIP CUSTOMISATION`. Be sure to set a username and password -- you will need them to log in to the IIAB Admin Console. Enable [SSH](https://www.baeldung.com/cs/ssh-intro) if you want shell access to IIAB later; otherwise leave it off.

7. Write the image to the microSD card, insert the card into your Raspberry Pi, and boot it.

The first boot may take a few minutes but generally no more than that.

If the `Internet in a Box` Wi-Fi network does not appear within a few minutes:

1. On an older Raspberry Pi or a large microSD card, first boot can take up to 15 minutes -- try waiting.

2. Unplug power, wait 5 seconds, and plug it back in.

3. Connect a keyboard and HDMI monitor, or plug into your router with wired Ethernet, then [SSH](https://www.baeldung.com/cs/ssh-intro) in as the user you created: `ssh username@box.local` (or `@box.lan`; or [use its IP address](https://www.raspberrypi.com/documentation/computers/remote-access.html#ip-address)) and run:

```sh
sudo iiab-hotspot-on
sudo iiab-network
sudo reboot
```

</details>

- FAQ: [FAQ.IIAB.IO](https://FAQ.IIAB.IO)
- Release Notes: https://github.com/iiab/iiab/wiki/IIAB-8.3-Release-Notes
- Contributors Guide: https://github.com/iiab/iiab/wiki/Contributors-Guide-(EN)
