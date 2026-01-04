# IIAB Patch Maintenance Guide

This simple guide shows you how to manage patches using the `maintain_patch.sh` script.

**Tool Location:** `/opt/iiab/iiab/scripts/maintain_patch.sh`

---

## What does this tool do?

It helps you safely edit the code in our patch files. Instead of editing the patch file directly (which is hard!), this tool:
1.  **Sets up** a temporary folder with the upstream source code.
2.  **Applies** your patch so you can see the code.
3.  **Updates** the patch file with your new changes when you are done.

---

## Quick Start: How to Edit a Patch

**Scenario:** You want to make a change to a file (e.g., `cps/web.py`) inside `0001-Fix-Login.patch` for **Calibre-Web**.

### Step 1: Setup
Run this command to prepare your workspace. It clones the code and applies the patch for you.

```bash
cd /opt/iiab/iiab/scripts
./maintain_patch.sh setup https://github.com/iiab/calibre-web.git ../roles/calibre-web/files/0001-Fix-Login.patch
```

*Output will tell you where your workspace is (e.g., `/tmp/iiab-patch-work-0`).*

### Step 2: Make Your Changes
Go to that folder and edit the files using your favorite editor.

```bash
cd /tmp/iiab-patch-work-0
nano cps/web.py
# Make your changes, save, and exit.
```

### Step 3: Finish (Save Changes)
Tell the script to save your changes back to the patch file.
**Important:** List the files you changed so the patch stays clean!

```bash
cd /opt/iiab/iiab/scripts
./maintain_patch.sh finish ../roles/calibre-web/files/0001-Fix-Login.patch cps/web.py
```

**Done!** Your patch file is now updated and clean.

---

## Other Useful Commands

### Cleaning Up Noise
If you accidentally messed up a patch file (e.g., permissions or "old mode" lines), just run this to clean it instantly:

```bash
./maintain_patch.sh clean-all /opt/iiab/iiab/roles/calibre-web/files/
```

### Updating to a New Version
If you need to move your patch to a newer version of Calibre-Web (e.g. `v0.6.19`):

1.  **Setup** (same as above).
2.  **Update**:
    ```bash
    ./maintain_patch.sh update v0.6.19
    ```
    *(If there are conflicts, git will ask you to fix them).*
3.  **Finish** (same as above).

---

## Troubleshooting

*   **"Patch file not found"**: Make sure you provide the full path to the `.patch` file.
*   **"Failed to apply patch"**: This means your patch conflicts with the code. Go to the workspace directory and check `git status`.
