import {Fill, Stroke, Style} from 'ol/style';
import 'ol/ol.css';
import GeoJSON from 'ol/format/GeoJSON';
import Map from 'ol/Map';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import View from 'ol/View';
//import XYZSource from 'ol/source/XYZ';
//import MVT from 'ol/format/MVT';

// a global variable to control which features are shown
var show = {};
var mapData = "/common/assets";


var map = new Map({
  target: 'map-container',
  layers: [
    new VectorLayer({
      source: new VectorSource({
        format: new GeoJSON(),
        url: mapData + '/countries.json'
      }),
      style: new Style({
        fill: new Fill({
          color: 'rgb(219, 180, 131)' 
        }),
        stroke: new Stroke({
          color: 'white'
        })
      })
    }),
    
  ],

  view: new View({
    center: [0, 0],
    zoom: 2
  })
});

var setBoxStyle = function(feature) {
  var name = feature.get("name");
  //alert(keys+'');
  if (typeof show !== 'undefined' &&
       show != null && name == show) {
    return new Style({
      fill: new Fill({
        color: 'rgba(67, 163, 46, 0.2)'
      }),
      stroke: new Stroke({
        color: 'rgba(67, 163, 46, 1)',
        width: 2
      })
    })
  } else {
    return new Style({
      fill: new Fill({
        color: 'rgba(255,255,255,.10)'
      }),
      stroke: new Stroke({
        color: 'rgba(255,255,255,.3)'
      })
    })
  }
}

var boxLayer = new VectorLayer({
  source: new VectorSource({
    format: new GeoJSON(),
    url: mapData + '/bboxes.geojson'
  }),
  id: 'boxes',
  style: setBoxStyle
});
map.addLayer(boxLayer);

$( document ).on("mouseover",".extract",function(){

  var data = JSON.parse($(this).attr('data-region'));
  show = data.name;
  //setBoxStyle();
  boxLayer.changed();
});
$( document ).on("mouseout",".extract",function(){
  var data = JSON.parse($(this).attr('data-region'));
  show = '';
  boxLayer.changed();
});
