## Objective

To streamline troubleshooting of remote Internet-in-a-Box (IIAB) installations, we bundle up common machine/software diagnostics, all together in 1 human-readable small file, that can be easily circulated online AND offline.

The ``pastebinit`` command can then be used to upload this file, creating a short URL that makes it easier to pass around.

But first off, the file is compiled by harvesting 5 main kinds of things:

1. Files specially requested (if you run ``iiab-diagnostics FILENAME1 FILENAME2``)

2. Regular Files

3. Content of Directories, 1-level deep

4. Output of Commands

5. Log Files: (last 100 lines of each)

## Usage 

1. Run it as follows:

   ```
   sudo iiab-diagnostics
   ```

   To bundle in more files, run:

   ```
   sudo iiab-diagnostics FILENAME1 FILENAME2
   ```

   ( This will bundle up all the diagnostics, into a new file placed in: /etc/iiab/diag/ )

2. Upload the file using the pastebinit command:

   ```
   pastebinit < /etc/iiab/diagnostics/<name of file you just created>
   ```
   
   This will generalte a link (URL).

3. Post the link (URL) to a "New issue" at https://github.com/iiab/iiab/issues

   Include a description of the symptoms, and how to reproduce the problem.

4. If you don't understand Step 3, email everything to bugs@iiab.io instead.

## Source Code

Please look over the bottom of [iiab-diagnostics](iiab-diagnostics) to learn more about which common IIAB files make rapid troubleshooting possible.
