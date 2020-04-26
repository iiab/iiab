#!/bin/bash -x

# This /opt/iiab/iiab/roles/httpd/templates/refresh-wiki-docs.sh becomes
# /usr/bin/iiab-refresh-wiki-docs during IIAB's install.

# This pulls down iiab/iiab repo's entire Tech Docs Wiki (and scrapes/downloads
# other docs!) to create IIAB's offline docs collection: http://box/info

# TO DO: find more pages to download/scrape and offline links to fix,
# based on "fieldback" from truly remote implementer/operators.

set -e                           # Exit on error (avoids snowballing)
source {{ iiab_env_file }}       # /etc/iiab/iiab.env
INPUT=/tmp/iiab-wiki
OUTPUT=/tmp/iiab-wiki.out
DESTPATH={{ doc_root }}/info     # /library/www/html/info
DOCSPATH=$DESTPATH/docs          # /library/www/html/info/docs

rm -rf $INPUT
rm -rf $OUTPUT
mkdir -p $INPUT
mkdir -p $OUTPUT
mkdir -p $DOCSPATH

git clone https://github.com/iiab/iiab.wiki.git $INPUT

for f in `ls $INPUT`; do
    FTRIMMED=${f%.md}
    if [ $FTRIMMED = "Home" ]; then FTRIMMED=index; fi
    pandoc -s $INPUT/$f -o $OUTPUT/$FTRIMMED.html
done

rsync -av $OUTPUT/ $DESTPATH

# Download FAQ etc
lynx -reload -source http://wiki.laptop.org/go/IIAB/FAQ > $DESTPATH/FAQ.html
lynx -reload -source http://wiki.laptop.org/go/IIAB/Security > $DESTPATH/Security.html
lynx -reload -source http://wiki.laptop.org/go/IIAB/local_vars.yml > $DESTPATH/local_vars.yml
lynx -reload -source http://wiki.laptop.org/go/IIAB/local_vars_min.yml > $DESTPATH/local_vars_min.yml
lynx -reload -source http://wiki.laptop.org/go/IIAB/local_vars_big.yml > $DESTPATH/local_vars_big.yml

# Download older release notes
lynx -reload -source https://github.com/XSCE/xsce/wiki/IIAB-6.2-Release-Notes > $DESTPATH/IIAB-6.2-Release-Notes.html
lynx -reload -source https://github.com/XSCE/xsce/blob/release-6.2/ReleaseNotes6.0.md > $DESTPATH/ReleaseNotes6.0.html
lynx -reload -source https://github.com/XSCE/xsce/blob/release-6.2/ReleaseNotes6.1.md > $DESTPATH/ReleaseNotes6.1.html

# Download Raspberry Pi guides
wget -nc https://www.raspberrypi.org/magpi-issues/Beginners_Guide_v1.pdf -O $DOCSPATH/Raspberry_Pi_Beginners_Guide_v1.pdf || true    # Overrides set -e
wget -nc https://ia601505.us.archive.org/15/items/other_doc/other_doc.pdf -O $DOCSPATH/Raspberry_Pi_User_Guide_v4.pdf || true

# Copy PDF from Lokole playbook
cp -p "{{ iiab_dir }}/roles/lokole/Lokole-IIAB_Users_Manual.pdf" $DOCSPATH    # From /opt/iiab/iiab

# MAKE LINKS REFER TO LOCAL ITEMS...

# ...on main page (http://box/info)
sed -i -r "s|https://www.raspberrypi.org/magpi-issues/Beginners_Guide_v1.pdf|docs/Raspberry_Pi_Beginners_Guide_v1.pdf|g" $DESTPATH/index.html
sed -i -r "s|https://ia601505.us.archive.org/15/items/other_doc/other_doc.pdf|docs/Raspberry_Pi_User_Guide_v4.pdf|g" $DESTPATH/index.html
sed -i -r "s|https://github.com/iiab/iiab/blob/master/roles/lokole/Lokole-IIAB_Users_Manual.pdf|docs/Lokole-IIAB_Users_Manual.pdf|g" $DESTPATH/index.html

# ...and within subpages
for f in $DESTPATH/*.html; do
    sed -i -r "s|https://github.com/iiab/iiab/wiki/([-.A-Za-z0-9]*)|\1.html|g" $f

    sed -i -e "s|https://github.com/xsce/xsce/blob/release-6.2/\(.*\)\.md\">|\1.html\">|g" $f
    sed -i -e "s|https://github.com/xsce/xsce/wiki/\(.*\)\">|\1.html\">|g" $f

    sed -i -e "s|http://wiki.laptop.org/go/IIAB/FAQ|FAQ.html|g" $f
    sed -i -e "s|/go/IIAB/FAQ|FAQ.html|g" $f
    sed -i -e "s|http://wiki.iiab.io/FAQ|FAQ.html|g" $f
    sed -i -e "s|http://FAQ.IIAB.IO|FAQ.html|g" $f
    sed -i -e "s|http://faq.iiab.io|FAQ.html|g" $f
    sed -i -e "s|http://schoolserver.org/FAQ|FAQ.html|g" $f
    sed -i -e "s|http://schoolserver.org/faq|FAQ.html|g" $f
    sed -i -e "s|http://wiki.laptop.org/go/XS_Community_Edition/FAQ|FAQ.html|g" $f

    sed -i -e "s|http://wiki.laptop.org/go/IIAB/Security|Security.html|g" $f
    sed -i -e "s|/go/IIAB/Security|Security.html|g" $f
    sed -i -e "s|http://wiki.iiab.io/Security|Security.html|g" $f

    sed -i -e "s|http://wiki.laptop.org/go/IIAB/local_vars.yml|local_vars.yml|g" $f
    sed -i -e "s|/go/IIAB/local_vars.yml|local_vars.yml|g" $f
    sed -i -e "s|http://wiki.iiab.io/local_vars.yml|local_vars.yml|g" $f

    sed -i -e "s|http://wiki.laptop.org/go/IIAB/local_vars_min.yml|local_vars_min.yml|g" $f
    sed -i -e "s|/go/IIAB/local_vars_min.yml|local_vars_min.yml|g" $f
    sed -i -e "s|http://wiki.iiab.io/local_vars_min.yml|local_vars_min.yml|g" $f

    sed -i -e "s|http://wiki.laptop.org/go/IIAB/local_vars_big.yml|local_vars_big.yml|g" $f
    sed -i -e "s|/go/IIAB/local_vars_big.yml|local_vars_big.yml|g" $f
    sed -i -e "s|http://wiki.iiab.io/local_vars_big.yml|local_vars_big.yml|g" $f
done

exit 0
