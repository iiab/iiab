## Objective

To streamline troubleshooting of remote Internet-in-a-Box (IIAB) installations, we bundle up common machine/software diagnostics, all together in 1 human-readable file of about 2000 lines, that can be easily circulated online AND offline.

Just FYI Raspberry Pi OS's [/usr/bin/raspinfo](https://github.com/raspberrypi/utils/blob/master/raspinfo/raspinfo) serves a very similar purpose, but we do not include that program's 700-to-800 line output at present.

For a more concise "instant" summary of any IIAB machine (about 20-25 lines) try this command instead: [/usr/bin/iiab-summary](iiab-summary)

## What `iiab-diagnostics` does

Passwords (including Wi-Fi passwords) are auto-redacted as the output file is generated, to protect your community confidentiality.

Finally, the ``pastebinit`` command can be used to auto-upload the output file (human-readable, approx 2000 lines) creating a short URL that makes it much easier to circulate among [volunteers](https://internet-in-a-box.org/contributing.html).

But first off, the file is compiled by harvesting 1 + 6 kinds of things:

0. Filename Header + Git Hashes + Raspberry Pi Model + OS + CPU Architecture(s)

1. Files specially requested (if you run ``sudo iiab-diagnostics PATH/FILE1 PATH/FILE2``)

2. Regular Files

3. Content of Directories (1-level deep)

4. Output of Commands

5. Firewall Rules

6. Log Files (last 100 lines of each)

## Usage 

1. Run it as follows:

   ```
   iiab-diagnostics
   ```

   Better yet, for [more complete results](https://github.com/iiab/iiab/pull/2000#issue-327506999), run it as root:

   ```
   sudo iiab-diagnostics
   ```

   To bundle in yet more files, run:

   ```
   sudo iiab-diagnostics PATH/FILE1 PATH/FILE2 ...
   ```

   ( All diagnostics will be bundled up into a single human-readable file, placed in: /etc/iiab/diag/ )

2. Make sure you're online, as you will be prompted to auto-publish your newly-compiled diagnostics file to a web pastebin.

   Or, you can later/manually upload it using the ``pastebinit`` command:

   ```
   pastebinit -b sprunge.us < /etc/iiab/diag/NEW-FILE-NAME
   ```

   Either way, this will generate an actual web link (URL).

3. Post this link (URL) to a "New issue" at https://github.com/iiab/iiab/issues

   Include a description of the symptoms, and how to reproduce the problem.

4. If you don't understand Step 3, email everything to bugs@iiab.io instead.

## Source Code

Please look over the bottom of [iiab-diagnostics](iiab-diagnostics) (lines 127-244 especially) to learn more about which common IIAB files and commands make this rapid troubleshooting possible.
