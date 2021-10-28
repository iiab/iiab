# Remote support of an Internet-in-a-Box using https://remote.it

Remote.it can be a great way to remotely support an Internet-in-a-Box (IIAB).  

For other approaches, please see http://FAQ.IIAB.IO -> "How can I remotely manage my Internet-in-a-Box?"

To install remote.it onto a Raspberry Pi IIAB:

1. Set `remoteit_install` and `remoteit_enabled` to `True` in your IIAB's [/etc/iiab/local_vars.yml](http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F)
2. Install it (remote.it) onto your IIAB, by running:
   ```
   cd /opt/iiab/iiab
   sudo ./runrole remoteit
   ```
   EXPLANATION: The above installs remote.it code, in a way that was originally designed to be interactive, and provide you the registration code needed to make remote connections to this IIAB.

3. To obtain this IIAB's remote.it registration code, run:
   ```
   sudo apt reinstall /opt/iiab/downloads/remoteit-4.13.5.armhf.rpi.deb
   ```
4. Record this registration code in a safe place, similar to a password!
5. After you've installed the https://remote.it client software onto a separate computer or device (e.g. your own laptop) click on the '+' icon, then enter the remote.it registration number (for the IIAB that you need to connect to).
