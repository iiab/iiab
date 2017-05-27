#!/bin/bash
rsync -a /library/working/zims/$1/data/content/ /library/zims/content
rsync -a /library/working/zims/$1/data/index/ /library/zims/index
/usr/bin/xsce-make-kiwix-lib
# rm -Rf /library/working/zims/$1
