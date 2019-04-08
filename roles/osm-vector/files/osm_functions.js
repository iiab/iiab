// osm_functions.js  -- (non authoritative see below) src = iiab/roles/files/
// copyright 2019 George Hunt
// CAUTION -- this file is duplicate to admin-console/console/files/js/osm_fuctions.js -- please think of admin-console as authoritative
//     Placed here in duplicate to ease debugging, and simplify dependences

var regionGeojson = {};
var regionList = [];
var regionInstalled = [];
var commonAssetsDir = '/common/assets/';
var mapAssetsDir = '/osm-vector/maplist/assets/';
var iiab_config_dir = '/etc/iiab/';
var onChangeFunc = "setSize";
var osmCatalog = {};

// following 2 lines an experiment to see if test page and console can be common
//var jquery = require("./assets/jquery.min");
//window.$ = window.jQuery = jquery;

function getOsmStat(){
  // called during the init
  console.log('in getOsmStat');
  readOsmCatalog( true ); // we want checkboxes
  readOsmIdx();
}
  
function readOsmIdx(){
	//consoleLog ("in readOsmIdx");
  var resp = $.ajax({
    type: 'GET',
    url: consoleJsonDir + 'osm-vector-idx.json',
    dataType: 'json'
  })
  .done(function( data ) {
  	osmInstalled = data['regions'];
   regionInstalled = [];
   for (region in data['regions']) {
    if (data['regions'].hasOwnProperty(region)) {
        regionInstalled.push(region);
    }
}
    //consoleLog(osmInstalled + '');
  })
  .fail(jsonErrhandler);

  return resp;
}

function readOsmCatalog(checkbox){
   checkbox = checkbox || true;
	console.log ("in readOsmCalalog");
   regionList = [];
  var resp = $.ajax({
    type: 'GET',
    url: mapAssetsDir + 'regions.json',
    dataType: 'json'
  })
  .done(function( data ) {
  	 regionJson = data;
    osmCatalog = regionJson['regions'];
    for(var key in osmCatalog){
      //console.log(key + '  ' + osmCatalog[key]['title']);
      osmCatalog[key]['name'] = key;
      regionList.push(osmCatalog[key]);
    }
  })
  .fail(jsonErrhandler);
  return resp;
}

function renderRegionList(checkbox) { // generic
	var html = "";
   // order the regionList by seq number
   var regions = regionList;
	console.log ("in renderRegionList");

	// sort on basis of seq
  regions = regions.sort(function(a,b){
    if (a.seq < b.seq) return -1;
    else return 1;
    });
  //console.log(regions);
	// render each region
   html += '<form>';
	regions.forEach((region, index) => { // now render the html
      //console.log(region.title + " " +region.seq);
      html += genRegionItem(region,checkbox);
  });
  html += '</form>';
  //console.log(html);
  $( "#regionlist" ).html(html);
}


function genRegionItem(region,checkbox) {
  var html = "";
  console.log("in genRegionItem: " + region.name);
  var itemId = region.title;
  var ksize = region.size / 1000;
//console.log(html);
  html += '<div  class="extract" data-region={"name":"' + region.name + '"}>';
  html += ' <label>';
  if ( checkbox ) {
      if (selectedOsmItems.indexOf(region.name) != -1)
         checked = 'checked';
      else
         checked = '';
      html += '<input type="checkbox" name="' + region.name + '"';
      html += ' onChange="updateOsmSpace(this)" ' + checked + '>';
  }
      html += itemId;
  if ( checkbox ) { html +=  '</input>';};
  html += '</label>'; // end input
  html += ' Size: ' + readableSize(ksize);
  html += '</div>';
  //console.log(html);

  return html;
}

function instOsmItem(name) {
  var command = "INST-OSM-VECT-SET";
  var cmd_args = {};
  cmd_args['osm_vect_id'] = name;
  cmd = command + " " + JSON.stringify(cmd_args);
  sendCmdSrvCmd(cmd, genericCmdHandler);
  osmDownloading.push(name);
  if ( osmWip.indexOf(name) != -1 )
     osmWip.push(osmCatalog[name]);
  console.log('osmWip: ' + osmWip);
  return true;
}

function jsonErrhandler (jqXHR, textStatus, errorThrown)
{
  // only handle json parse errors here, others in ajaxErrHandler
  if (textStatus == "parserror") {
    //alert ("Json Errhandler: " + textStatus + ", " + errorThrown);
    displayServerCommandStatus("Json Errhandler: " + textStatus + ", " + errorThrown);
  }
  //consoleLog("In Error Handler logging jqXHR");
  console.log(textStatus);
  console.log(errorThrown);
  console.log(jqXHR);

  return false;
}

function readableSize(kbytes) {
  if (kbytes == 0)
  return "0";
  var bytes = 1024 * kbytes;
  var s = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'];
  var e = Math.floor(Math.log(bytes) / Math.log(1024));
  return (bytes / Math.pow(1024, e)).toFixed(2) + " " + s[e];
}

function updateOsmSpace(cb){
  console.log("in updateOsmSpace" + cb);
  var region = cb.name;
  updateOsmSpaceUtil(region, cb.checked);
}

function updateOsmSpaceUtil(region, checked){
  var size =  parseInt(osmCatalog[region].size);

  var modIdx = selectedOsmItems.indexOf(region);

  if (checked){
    if (regionInstalled.indexOf(region) == -1){ // only update if not already installed mods
      sysStorage.osm_selected_size += size;
      selectedOsmItems.push(region);
    }
  }
  else {
    if (modIdx != -1){
      sysStorage.osm_selected_size -= size;
      selectedOsmItems.splice(modIdx, 1);
    }
  }
  
  displaySpaceAvail();
}

/*
function totalSpace(){
  // obsolete but perhaps useful in debugging since it worked
  var sum = 0;
  $( ".extract" ).each(function(ind,elem){
    var data = JSON.parse($(this).attr('data-region'));
    var region = data.name;
    var size = parseInt(osmCatalog[region]['size']);
    var chk = $( this ).find(':checkbox').prop("checked") == true;
    if (chk && typeof size !== 'undefined')
        sum += size;
    });
   var ksize = sum / 1000;
  $( "#osmDiskSpace" ).html(readableSize(ksize));
}

$( '#instOsmRegion').on('click', function(evnt){
   readOsmCatalog();
   osm.render();
});
*/
function renderOsm(){
   console.log('in renderOsm');
   window.map.setTarget($("#osm-container")[0]);
   window.map.render();
   renderRegionList(true);
}
function initOsm(){
var dummy = 0;
   sysStorage.osm_selected_size = 0;
   $.when(readOsmCatalog(true)).then(renderRegionList);
}

