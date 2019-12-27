## Restructure of Map Packages
1. Separate viewer program functions from map data, and install them separately.
2. Use sql functions to combine map data (to zoom level 10) with more detailed regional data to zoom 18.
3. Add back in the San Jose region for testing purposes. 
4. Increase the base install from zoom 9 to 10, so that city search is successful more of the time.
5. Include a hash in the installed map data, to facilitate combination of base map and regional data.
6. Provide a command line tool to increase regional satellite data from zoom 9 to 13.
