#!/bin/bash 
# get the max an min for x and y at tach zoom level and count tiles per zoom
if [ $# -eq 0 ]; then
   echo First paramater is sqlite database path
   exit 1
fi
cat << EOF | sqlite3 $1
.headers on
select zoom_level, max(tile_row),min(tile_row),max(tile_column),min(tile_column), count(zoom_level) from map  group by zoom_level;
EOF
