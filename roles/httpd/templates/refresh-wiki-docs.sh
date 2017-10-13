#!/bin/bash -x

# Pull down repo's entire wiki (and similar) to create offline docs

set -e
source /etc/iiab/iiab.env
INPUT=/tmp/iiab-wiki
OUTPUT=/tmp/iiab-wiki.out
DESTPATH=/library/www/html/info

rm -rf $INPUT
rm -rf $OUTPUT
mkdir -p $INPUT
mkdir -p $OUTPUT

git clone https://github.com/iiab/iiab.wiki.git $INPUT

for f in `ls $INPUT`; do
    FTRIMMED=${f%.md}
    if [ $FTRIMMED = "Home" ]; then FTRIMMED=index; fi
    pandoc -s $INPUT/$f -o $OUTPUT/$FTRIMMED.html
done

rsync -av $OUTPUT/ $DESTPATH

# To Do: find more pages to d/l and offline links to fix, based on "fieldback" from truly remote implementer/operators

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

# Make links refer to local items
for f in `ls $DESTPATH`; do
    sed -i -r "s|https://github.com/iiab/iiab/wiki/([-.0-9A-z]*)|\1.html|g" $DESTPATH/$f

    sed -i -e "s|https://github.com/xsce/xsce/blob/release-6.2/\(.*\)\.md\">|\1.html\">|g" $DESTPATH/$f
    sed -i -e "s|https://github.com/xsce/xsce/wiki/\(.*\)\">|\1.html\">|g" $DESTPATH/$f

    sed -i -e "s|http://wiki.laptop.org/go/IIAB/FAQ|FAQ.html|g" $DESTPATH/$f
    sed -i -e "s|/go/IIAB/FAQ|FAQ.html|g" $DESTPATH/$f
    sed -i -e "s|http://wiki.iiab.io/FAQ|FAQ.html|g" $DESTPATH/$f
    sed -i -e "s|http://FAQ.IIAB.IO|FAQ.html|g" $DESTPATH/$f
    sed -i -e "s|http://faq.iiab.io|FAQ.html|g" $DESTPATH/$f
    sed -i -e "s|http://schoolserver.org/FAQ|FAQ.html|g" $DESTPATH/$f
    sed -i -e "s|http://schoolserver.org/faq|FAQ.html|g" $DESTPATH/$f
    sed -i -e "s|http://wiki.laptop.org/go/XS_Community_Edition/FAQ|FAQ.html|g" $DESTPATH/$f

    sed -i -e "s|http://wiki.laptop.org/go/IIAB/Security|Security.html|g" $DESTPATH/$f
    sed -i -e "s|/go/IIAB/Security|Security.html|g" $DESTPATH/$f
    sed -i -e "s|http://wiki.iiab.io/Security|Security.html|g" $DESTPATH/$f

    sed -i -e "s|http://wiki.laptop.org/go/IIAB/local_vars.yml|local_vars.yml|g" $DESTPATH/$f
    sed -i -e "s|/go/IIAB/local_vars.yml|local_vars.yml|g" $DESTPATH/$f
    sed -i -e "s|http://wiki.iiab.io/local_vars.yml|local_vars.yml|g" $DESTPATH/$f

    sed -i -e "s|http://wiki.laptop.org/go/IIAB/local_vars_min.yml|local_vars_min.yml|g" $DESTPATH/$f
    sed -i -e "s|/go/IIAB/local_vars_min.yml|local_vars_min.yml|g" $DESTPATH/$f
    sed -i -e "s|http://wiki.iiab.io/local_vars_min.yml|local_vars_min.yml|g" $DESTPATH/$f

    sed -i -e "s|http://wiki.laptop.org/go/IIAB/local_vars_big.yml|local_vars_big.yml|g" $DESTPATH/$f
    sed -i -e "s|/go/IIAB/local_vars_big.yml|local_vars_big.yml|g" $DESTPATH/$f
    sed -i -e "s|http://wiki.iiab.io/local_vars_big.yml|local_vars_big.yml|g" $DESTPATH/$f
done

exit 0
