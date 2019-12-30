<?php

/*
 * TileServer.php project
 * ======================
 * https://github.com/klokantech/tileserver-php/
 * Copyright (C) 2016 - Klokan Technologies GmbH
 */

global $config;
$config['serverTitle'] = 'Maps hosted with TileServer-php v2.0';
$config['availableFormats'] = array('png', 'jpg', 'jpeg', 'gif', 'webp', 'pbf', 'hybrid');
$config['dataRoot'] = '';
//$config['template'] = 'template.php';
//$config['baseUrls'] = array('t0.server.com', 't1.server.com');

Router::serve(array(
    '/' => 'Server:getHtml',
    '/maps' => 'Server:getInfo',
    '/html' => 'Server:getHtml',
    '/:alpha/:number/:number/:number.grid.json' => 'Json:getUTFGrid',
    '/:alpha.json' => 'Json:getJson',
    '/:alpha.jsonp' => 'Json:getJsonp',
    '/wmts' => 'Wmts:get',
    '/wmts/1.0.0/WMTSCapabilities.xml' => 'Wmts:get',
    '/wmts/:alpha/:number/:number/:alpha' => 'Wmts:getTile',
    '/wmts/:alpha/:alpha/:number/:number/:alpha' => 'Wmts:getTile',
    '/wmts/:alpha/:alpha/:alpha/:number/:number/:alpha' => 'Wmts:getTile',
    '/:alpha/:number/:number/:alpha' => 'Wmts:getTile',
    '/tms' => 'Tms:getCapabilities',
    '/tms/:alpha' => 'Tms:getLayerCapabilities',
));

/**
 * Server base
 */
class Server {

  /**
   * Configuration of TileServer [baseUrls, serverTitle]
   * @var array
   */
  public $config;

  /**
   * Datasets stored in file structure
   * @var array
   */
  public $fileLayer = array();

  /**
   * Datasets stored in database
   * @var array
   */
  public $dbLayer = array();

  /**
   * PDO database connection
   * @var object
   */
  public $db;

  /**
   * Set config
   */
  public function __construct() {
    $this->config = $GLOBALS['config'];

    if($this->config['dataRoot'] != ''
       && substr($this->config['dataRoot'], -1) != '/' ){
      $this->config['dataRoot'] .= '/';
    }

    //Get config from enviroment
    $envServerTitle = getenv('serverTitle');
    if($envServerTitle !== false){
      $this->config['serverTitle'] = $envServerTitle;
    }
    $envBaseUrls = getenv('baseUrls');
    if($envBaseUrls !== false){
      $this->config['baseUrls'] = is_array($envBaseUrls) ?
              $envBaseUrls : explode(',', $envBaseUrls);
    }
    $envTemplate = getenv('template');
    if($envBaseUrls !== false){
      $this->config['template'] = $envTemplate;
    }
  }

  /**
   * Looks for datasets
   */
  public function setDatasets() {
    $mjs = glob('*/metadata.json');
    $mbts = glob($this->config['dataRoot'] . '*.mbtiles');
    if ($mjs) {
      foreach (array_filter($mjs, 'is_readable') as $mj) {
        $layer = $this->metadataFromMetadataJson($mj);
        array_push($this->fileLayer, $layer);
      }
    }
    if ($mbts) {
      foreach (array_filter($mbts, 'is_readable') as $mbt) {
        $this->dbLayer[] = $this->metadataFromMbtiles($mbt);
      }
    }
  }

  /**
   * Processing params from router <server>/<layer>/<z>/<x>/<y>.ext
   * @param array $params
   */
  public function setParams($params) {
    if (isset($params[1])) {
      $this->layer = $params[1];
    }
    $params = array_reverse($params);
    if (isset($params[2])) {
      $this->z = $params[2];
      $this->x = $params[1];
      $file = explode('.', $params[0]);
      $this->y = $file[0];
      $this->ext = isset($file[1]) ? $file[1] : null;
    }
  }

  /**
   * Get variable don't independent on sensitivity
   * @param string $key
   * @return boolean
   */
  public function getGlobal($isKey) {
    $get = $_GET;
    foreach ($get as $key => $value) {
      if (strtolower($isKey) == strtolower($key)) {
        return $value;
      }
    }
    return false;
  }

  /**
   * Testing if is a database layer
   * @param string $layer
   * @return boolean
   */
  public function isDBLayer($layer) {
    if (is_file($this->config['dataRoot'] . $layer . '.mbtiles')) {
      return true;
    } else {
      return false;
    }
  }

  /**
   * Testing if is a file layer
   * @param string $layer
   * @return boolean
   */
  public function isFileLayer($layer) {
    if (is_dir($layer)) {
      return true;
    } else {
      return false;
    }
  }

  /**
   * Get metadata from metadataJson
   * @param string $jsonFileName
   * @return array
   */
  public function metadataFromMetadataJson($jsonFileName) {
    $metadata = json_decode(file_get_contents($jsonFileName), true);
    $metadata['basename'] = str_replace('/metadata.json', '', $jsonFileName);
    return $this->metadataValidation($metadata);
  }

  /**
   * Loads metadata from MBtiles
   * @param string $mbt
   * @return object
   */
  public function metadataFromMbtiles($mbt) {
    $metadata = array();
    $this->DBconnect($mbt);
    $result = $this->db->query('select * from metadata');

    $resultdata = $result->fetchAll();
    foreach ($resultdata as $r) {
      $value = preg_replace('/(\\n)+/', '', $r['value']);
      $metadata[$r['name']] = addslashes($value);
    }
    if (!array_key_exists('minzoom', $metadata)
    || !array_key_exists('maxzoom', $metadata)
    ) {
      // autodetect minzoom and maxzoom
      $result = $this->db->query('select min(zoom_level) as min, max(zoom_level) as max from tiles');
      $resultdata = $result->fetchAll();
      if (!array_key_exists('minzoom', $metadata)){
        $metadata['minzoom'] = $resultdata[0]['min'];
      }
      if (!array_key_exists('maxzoom', $metadata)){
        $metadata['maxzoom'] = $resultdata[0]['max'];
      }
    }
    // autodetect format using JPEG magic number FFD8
    if (!array_key_exists('format', $metadata)) {
      $result = $this->db->query('select hex(substr(tile_data,1,2)) as magic from tiles limit 1');
      $resultdata = $result->fetchAll();
      $metadata['format'] = ($resultdata[0]['magic'] == 'FFD8')
        ? 'jpg'
        : 'png';
    }
    // autodetect bounds
    if (!array_key_exists('bounds', $metadata)) {
      $result = $this->db->query('select min(tile_column) as w, max(tile_column) as e, min(tile_row) as s, max(tile_row) as n from tiles where zoom_level='.$metadata['maxzoom']);
      $resultdata = $result->fetchAll();
      $w = -180 + 360 * ($resultdata[0]['w'] / pow(2, $metadata['maxzoom']));
      $e = -180 + 360 * ((1 + $resultdata[0]['e']) / pow(2, $metadata['maxzoom']));
      $n = $this->row2lat($resultdata[0]['n'], $metadata['maxzoom']);
      $s = $this->row2lat($resultdata[0]['s'] - 1, $metadata['maxzoom']);
      $metadata['bounds'] = implode(',', array($w, $s, $e, $n));
    }
    $mbt = explode('.', $mbt);
    $metadata['basename'] = $mbt[0];
    $metadata = $this->metadataValidation($metadata);
    return $metadata;
  }

  /**
   * Convert row number to latitude of the top of the row
   * @param integer $r
   * @param integer $zoom
   * @return integer
   */
   public function row2lat($r, $zoom) {
     $y = $r / pow(2, $zoom - 1 ) - 1;
     return rad2deg(2.0 * atan(exp(3.191459196 * $y)) - 1.57079632679489661922);
   }

  /**
   * Valids metaJSON
   * @param object $metadata
   * @return object
   */
  public function metadataValidation($metadata) {
    if (!array_key_exists('bounds', $metadata)) {
      $metadata['bounds'] = array(-180, -85.06, 180, 85.06);
    } elseif (!is_array($metadata['bounds'])) {
      $metadata['bounds'] = array_map('floatval', explode(',', $metadata['bounds']));
    }
    if (!array_key_exists('profile', $metadata)) {
      $metadata['profile'] = 'mercator';
    }
    if (array_key_exists('minzoom', $metadata)){
      $metadata['minzoom'] = intval($metadata['minzoom']);
    }else{
      $metadata['minzoom'] = 0;
    }
    if (array_key_exists('maxzoom', $metadata)){
      $metadata['maxzoom'] = intval($metadata['maxzoom']);
    }else{
      $metadata['maxzoom'] = 18;
    }
    if (!array_key_exists('format', $metadata)) {
      if(array_key_exists('tiles', $metadata)){
        $pos = strrpos($metadata['tiles'][0], '.');
        $metadata['format'] = trim(substr($metadata['tiles'][0], $pos + 1));
      }
    }
    $formats = $this->config['availableFormats'];
    if(!in_array(strtolower($metadata['format']), $formats)){
        $metadata['format'] = 'png';
    }
    if (!array_key_exists('scale', $metadata)) {
      $metadata['scale'] = 1;
    }
    if(!array_key_exists('tiles', $metadata)){
      $tiles = array();
      foreach ($this->config['baseUrls'] as $url) {
        $url = '' . $this->config['protocol'] . '://' . $url . '/' .
                $metadata['basename'] . '/{z}/{x}/{y}';
        if(strlen($metadata['format']) <= 4){
          $url .= '.' . $metadata['format'];
        }
        $tiles[] = $url;
      }
      $metadata['tiles'] = $tiles;
    }
    return $metadata;
  }

  /**
   * SQLite connection
   * @param string $tileset
   */
  public function DBconnect($tileset) {
    try {
      $this->db = new PDO('sqlite:' . $tileset, '', '', array(PDO::ATTR_PERSISTENT => true));
    } catch (Exception $exc) {
      echo $exc->getTraceAsString();
      die;
    }

    if (!isset($this->db)) {
      header('Content-type: text/plain');
      echo 'Incorrect tileset name: ' . $tileset;
      die;
    }
  }

  /**
   * Check if file is modified and set Etag headers
   * @param string $filename
   * @return boolean
   */
  public function isModified($filename) {
    $filename = $this->config['dataRoot'] . $filename . '.mbtiles';
    $lastModifiedTime = filemtime($filename);
    $eTag = md5($lastModifiedTime);
    header('Last-Modified: ' . gmdate('D, d M Y H:i:s', $lastModifiedTime) . ' GMT');
    header('Etag:' . $eTag);
    if (@strtotime($_SERVER['HTTP_IF_MODIFIED_SINCE']) == $lastModifiedTime ||
            @trim($_SERVER['HTTP_IF_NONE_MATCH']) == $eTag) {
      return true;
    } else {
      return false;
    }
  }

  /**
   * Returns tile of dataset
   * @param string $tileset
   * @param integer $z
   * @param integer $y
   * @param integer $x
   * @param string $ext
   */
  public function renderTile($tileset, $z, $y, $x, $ext) {
    if ($this->isDBLayer($tileset)) {
      if ($this->isModified($tileset) == true) {
        header('Access-Control-Allow-Origin: *');
        header('HTTP/1.1 304 Not Modified');
        die;
      }
      $this->DBconnect($this->config['dataRoot'] . $tileset . '.mbtiles');
      $z = floatval($z);
      $y = floatval($y);
      $x = floatval($x);
      $flip = true;
      if ($flip) {
        $y = pow(2, $z) - 1 - $y;
      }
      $result = $this->db->query('select tile_data as t from tiles where zoom_level=' . $z . ' and tile_column=' . $x . ' and tile_row=' . $y);
      $data = $result->fetchColumn();
      if (!isset($data) || $data === false) {
        //if tile doesn't exist
        //select scale of tile (for retina tiles)
        $result = $this->db->query('select value from metadata where name="scale"');
        $resultdata = $result->fetchColumn();
        $scale = isset($resultdata) && $resultdata !== false ? $resultdata : 1;
        $this->getCleanTile($scale, $ext);
      } else {
        $result = $this->db->query('select value from metadata where name="format"');
        $resultdata = $result->fetchColumn();
        $format = isset($resultdata) && $resultdata !== false ? $resultdata : 'png';
        if ($format == 'jpg') {
          $format = 'jpeg';
        }
        if ($format == 'pbf') {
          header('Content-type: application/x-protobuf');
          header('Content-Encoding:gzip');
        } else {
          header('Content-type: image/' . $format);
        }
        header('Access-Control-Allow-Origin: *');
        echo $data;
      }
    } elseif ($this->isFileLayer($tileset)) {
      $name = './' . $tileset . '/' . $z . '/' . $x . '/' . $y;
      $mime = 'image/';
      if($ext != null){
        $name .= '.' . $ext;
      }
      if ($fp = @fopen($name, 'rb')) {
        if($ext != null){
          $mime .= $ext;
        }else{
          //detect image type from file
          $mimetypes = array('gif', 'jpeg', 'png');
          $mime .= $mimetypes[exif_imagetype($name) - 1];
        }
        header('Access-Control-Allow-Origin: *');
        header('Content-Type: ' . $mime);
        header('Content-Length: ' . filesize($name));
        fpassthru($fp);
        die;
      } else {
        //scale of tile (for retina tiles)
        $meta = json_decode(file_get_contents($tileset . '/metadata.json'));
        if(!isset($meta->scale)){
          $meta->scale = 1;
        }
      }
      $this->getCleanTile($meta->scale, $ext);
    } else {
      header('HTTP/1.1 404 Not Found');
      echo 'Server: Unknown or not specified dataset "' . $tileset . '"';
      die;
    }
  }

  /**
   * Returns clean tile
   * @param integer $scale Default 1
   */
  public function getCleanTile($scale = 1, $format = 'png') {
    switch ($format) {
      case 'pbf':
        header('Access-Control-Allow-Origin: *');
        header('HTTP/1.1 204 No Content');
        header('Content-Type: application/json; charset=utf-8');
        break;
      case 'webp':
        header('Access-Control-Allow-Origin: *');
        header('Content-type: image/webp');
        echo base64_decode('UklGRhIAAABXRUJQVlA4TAYAAAAvQWxvAGs=');
        break;
      case 'jpg':
        header('Access-Control-Allow-Origin: *');
        header('Content-type: image/jpg');
        echo base64_decode('/9j/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/yQALCAABAAEBAREA/8wABgAQEAX/2gAIAQEAAD8A0s8g/9k=');
        break;
      case 'png':
      default:
        header('Access-Control-Allow-Origin: *');
        header('Content-type: image/png');
        // 256x256 transparent optimised png tile
        echo unpack('H', '89504e470d0a1a0a0000000d494844520000010000000100010300000066bc3a2500000003504c5445000000a77a3dda0000000174524e530040e6d8660000001f494441541819edc1010d000000c220fba77e0e37600000000000000000e70221000001f5a2bd040000000049454e44ae426082');
        break;
    }
    die;
  }

  /**
   * Returns tile's UTFGrid
   * @param string $tileset
   * @param integer $z
   * @param integer $y
   * @param integer $x
   */
  public function renderUTFGrid($tileset, $z, $y, $x, $flip = true) {
    if ($this->isDBLayer($tileset)) {
      if ($this->isModified($tileset) == true) {
        header('HTTP/1.1 304 Not Modified');
      }
      if ($flip) {
        $y = pow(2, $z) - 1 - $y;
      }
      try {
        $this->DBconnect($this->config['dataRoot'] . $tileset . '.mbtiles');

        $query = 'SELECT grid FROM grids WHERE tile_column = ' . $x . ' AND '
                . 'tile_row = ' . $y . ' AND zoom_level = ' . $z;
        $result = $this->db->query($query);
        $data = $result->fetch(PDO::FETCH_ASSOC);

        if ($data !== false) {
          $grid = gzuncompress($data['grid']);
          $grid = substr(trim($grid), 0, -1);

          //adds legend (data) to output
          $grid .= ',"data":{';
          $kquery = 'SELECT key_name as key, key_json as json FROM grid_data '
                  . 'WHERE zoom_level=' . $z . ' and '
                  . 'tile_column=' . $x . ' and tile_row=' . $y;
          $result = $this->db->query($kquery);
          while ($r = $result->fetch(PDO::FETCH_ASSOC)) {
            $grid .= '"' . $r['key'] . '":' . $r['json'] . ',';
          }
          $grid = rtrim($grid, ',') . '}}';
          header('Access-Control-Allow-Origin: *');

          if (isset($_GET['callback']) && !empty($_GET['callback'])) {
            header('Content-Type:text/javascript charset=utf-8');
            echo $_GET['callback'] . '(' . $grid . ');';
          } else {
            header('Content-Type:text/javascript; charset=utf-8');
            echo $grid;
          }
        } else {
          header('Access-Control-Allow-Origin: *');
          echo '{}';
          die;
        }
      } catch (Exception $e) {
        header('Content-type: text/plain');
        print 'Error querying the database: ' . $e->getMessage();
      }
    } else {
      echo 'Server: no MBTiles tileset';
      die;
    }
  }

  /**
   * Returns server info
   */
  public function getInfo() {
    $this->setDatasets();
    $maps = array_merge($this->fileLayer, $this->dbLayer);
    header('Content-Type: text/html;charset=UTF-8');
    echo '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>' . $this->config['serverTitle'] . '</title></head><body>' .
      '<h1>' . $this->config['serverTitle'] . '</h1>' .
      'TileJSON service: <a href="//' . $this->config['baseUrls'][0] . '/index.json">' . $this->config['baseUrls'][0] . '/index.json</a><br>' .
      'WMTS service: <a href="//' . $this->config['baseUrls'][0] . '/wmts">' . $this->config['baseUrls'][0] . '/wmts</a><br>' .
      'TMS service: <a href="//' . $this->config['baseUrls'][0] . '/tms">' . $this->config['baseUrls'][0] . '/tms</a>';
    foreach ($maps as $map) {
      $extend = '[' . implode($map['bounds'], ', ') . ']';
      echo '<p>Tileset: <b>' . $map['basename'] . '</b><br>' .
        'Metadata: <a href="//' . $this->config['baseUrls'][0] . '/' . $map['basename'] . '.json">' .
        $this->config['baseUrls'][0] . '/' . $map['basename'] . '.json</a><br>' .
        'Bounds: ' . $extend ;
      if(isset($map['crs'])){echo '<br>CRS: ' . $map['crs'];}
       echo '</p>';
    }
    echo '<p>Copyright (C) 2016 - Klokan Technologies GmbH</p>';
    echo '</body></html>';
  }

  /**
   * Returns html viewer
   */
  public function getHtml() {
    $this->setDatasets();
    $maps = array_merge($this->fileLayer, $this->dbLayer);
    if (isset($this->config['template']) && file_exists($this->config['template'])) {
      $baseUrls = $this->config['baseUrls'];
      $serverTitle = $this->config['serverTitle'];
      include_once $this->config['template'];
    } else {
      header('Content-Type: text/html;charset=UTF-8');
      echo '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>' . $this->config['serverTitle'] . '</title>';
      echo '<link rel="stylesheet" type="text/css" href="//cdn.klokantech.com/tileviewer/v1/index.css" />
            <script src="//cdn.klokantech.com/tileviewer/v1/index.js"></script><body>
            <script>tileserver({index:"' . $this->config['protocol'] . '://' . $this->config['baseUrls'][0] . '/index.json", tilejson:"' . $this->config['protocol'] . '://' . $this->config['baseUrls'][0] . '/%n.json", tms:"' . $this->config['protocol'] . '://' . $this->config['baseUrls'][0] . '/tms", wmts:"' . $this->config['protocol'] . '://' . $this->config['baseUrls'][0] . '/wmts"});</script>
            <h1>Welcome to ' . $this->config['serverTitle'] . '</h1>
            <p>This server distributes maps to desktop, web, and mobile applications.</p>
            <p>The mapping data are available as OpenGIS Web Map Tiling Service (OGC WMTS), OSGEO Tile Map Service (TMS), and popular XYZ urls described with TileJSON metadata.</p>';
      if (!isset($maps)) {
        echo '<h3 style="color:darkred;">No maps available yet</h3>
              <p style="color:darkred; font-style: italic;">
              Ready to go - just upload some maps into directory:' . getcwd() . '/ on this server.</p>
              <p>Note: The maps can be a directory with tiles in XYZ format with metadata.json file.<br/>
              You can easily convert existing geodata (GeoTIFF, ECW, MrSID, etc) to this tile structure with <a href="http://www.maptiler.com">MapTiler Cluster</a> or open-source projects such as <a href="http://www.klokan.cz/projects/gdal2tiles/">GDAL2Tiles</a> or <a href="http://www.maptiler.org/">MapTiler</a> or simply upload any maps in MBTiles format made by <a href="http://www.tilemill.com/">TileMill</a>. Helpful is also the <a href="https://github.com/mapbox/mbutil">mbutil</a> tool. Serving directly from .mbtiles files is supported, but with decreased performance.</p>';
      } else {
        echo '<ul>';
        foreach ($maps as $map) {
          echo "<li>" . $map['name'] . '</li>';
        }
        echo '</ul>';
      }
      echo '</body></html>';
    }
  }

}

/**
 * JSON service
 */
class Json extends Server {

  /**
   * Callback for JSONP default grid
   * @var string
   */
  private $callback = 'grid';

  /**
   * @param array $params
   */
  public $layer = 'index';

  /**
   * @var integer
   */
  public $z;

  /**
   * @var integer
   */
  public $y;

  /**
   * @var integer
   */
  public $x;

  /**
   * @var string
   */
  public $ext;

  /**
   *
   * @param array $params
   */
  public function __construct($params) {
    parent::__construct();
    parent::setParams($params);
    if (isset($_GET['callback']) && !empty($_GET['callback'])) {
      $this->callback = $_GET['callback'];
    }
  }

  /**
   * Adds metadata about layer
   * @param array $metadata
   * @return array
   */
  public function metadataTileJson($metadata) {
    $metadata['tilejson'] = '2.0.0';
    $metadata['scheme'] = 'xyz';
    if ($this->isDBLayer($metadata['basename'])) {
      $this->DBconnect($this->config['dataRoot'] . $metadata['basename'] . '.mbtiles');
      $res = $this->db->query('SELECT name FROM sqlite_master WHERE name="grids";');
      if ($res) {
        foreach ($this->config['baseUrls'] as $url) {
          $grids[] = '' . $this->config['protocol'] . '://' . $url . '/' . $metadata['basename'] . '/{z}/{x}/{y}.grid.json';
        }
        $metadata['grids'] = $grids;
      }
    }
    if (array_key_exists('json', $metadata)) {
      $mjson = json_decode(stripslashes($metadata['json']));
      foreach ($mjson as $key => $value) {
        if ($key != 'Layer'){
          $metadata[$key] = $value;
        }
      }
      unset($metadata['json']);
    }
    return $metadata;
  }

  /**
   * Creates JSON from array
   * @param string $basename
   * @return string
   */
  private function createJson($basename) {
    $maps = array_merge($this->fileLayer, $this->dbLayer);
    if ($basename == 'index') {
      $output = '[';
      foreach ($maps as $map) {
        $output = $output . json_encode($this->metadataTileJson($map)) . ',';
      }
      if (strlen($output) > 1) {
        $output = substr_replace($output, ']', -1);
      } else {
        $output = $output . ']';
      }
    } else {
      foreach ($maps as $map) {
        if (strpos($map['basename'], $basename) !== false) {
          $output = json_encode($this->metadataTileJson($map));
          break;
        }
      }
    }
    if (!isset($output)) {
      echo 'TileServer: unknown map ' . $basename;
      die;
    }
    return stripslashes($output);
  }

  /**
   * Returns JSON with callback
   */
  public function getJson() {
    parent::setDatasets();
    header('Access-Control-Allow-Origin: *');
    header('Content-Type: application/json; charset=utf-8');
    if ($this->callback !== 'grid') {
      echo $this->callback . '(' . $this->createJson($this->layer) . ');'; die;
    } else {
      echo $this->createJson($this->layer); die;
    }
  }

  /**
   * Returns JSONP with callback
   */
  public function getJsonp() {
    parent::setDatasets();
    header('Access-Control-Allow-Origin: *');
    header('Content-Type: application/javascript; charset=utf-8');
    echo $this->callback . '(' . $this->createJson($this->layer) . ');';
  }

  /**
   * Returns UTFGrid in JSON format
   */
  public function getUTFGrid() {
    parent::renderUTFGrid($this->layer, $this->z, $this->y, $this->x);
  }

}

/**
 * Web map tile service
 */
class Wmts extends Server {

  /**
   * @param array $params
   */
  public $layer;

  /**
   * @var integer
   */
  public $z;

  /**
   * @var integer
   */
  public $y;

  /**
   * @var integer
   */
  public $x;

  /**
   * @var string
   */
  public $ext;

  /**
   *
   * @param array $params
   */
  public function __construct($params) {
    parent::__construct();
    if (isset($params)) {
      parent::setParams($params);
    }
  }

  /**
   * Tests request from url and call method
   */
  public function get() {
    $request = $this->getGlobal('Request');
    if ($request !== false && $request == 'gettile') {
      $this->getTile();
    } else {
      parent::setDatasets();
      $this->getCapabilities();
    }
  }

  /**
   * Validates tilematrixset, calculates missing params
   * @param Object $tileMatrix
   * @return Object
   */
  public function parseTileMatrix($layer, $tileMatrix){

    //process projection
    if(isset($layer['proj4'])){
      preg_match_all("/([^+= ]+)=([^= ]+)/", $layer['proj4'], $res);
      $proj4 = array_combine($res[1], $res[2]);
    }

    for($i = 0; $i < count($tileMatrix); $i++){

      if(!isset($tileMatrix[$i]['id'])){
        $tileMatrix[$i]['id'] =  (string) $i;
      }
      if (!isset($tileMatrix[$i]['extent']) && isset($layer['extent'])) {
        $tileMatrix[$i]['extent'] = $layer['extent'];
      }
      if (!isset($tileMatrix[$i]['matrix_size'])) {
        $tileExtent = $this->tilesOfExtent(
              $tileMatrix[$i]['extent'],
              $tileMatrix[$i]['origin'],
              $tileMatrix[$i]['pixel_size'],
              $tileMatrix[$i]['tile_size']
        );
        $tileMatrix[$i]['matrix_size'] = array(
            $tileExtent[2] + 1,
            $tileExtent[1] + 1
        );
      }
      if(!isset($tileMatrix[$i]['origin']) && isset($tileMatrix[$i]['extent'])){
        $tileMatrix[$i]['origin'] = array(
            $tileMatrix[$i]['extent'][0], $tileMatrix[$i]['extent'][3]
        );
      }
      // Origins of geographic coordinate systems are setting in opposite order
      if (isset($proj4) && $proj4['proj'] === 'longlat') {
        $tileMatrix[$i]['origin'] = array_reverse($tileMatrix[$i]['origin']);
      }
      if(!isset($tileMatrix[$i]['scale_denominator'])){
        $tileMatrix[$i]['scale_denominator'] = count($tileMatrix) - $i;
      }
      if(!isset($tileMatrix[$i]['tile_size'])){
        $tileSize = 256 * (int) $layer['scale'];
        $tileMatrix[$i]['tile_size'] = array($tileSize, $tileSize);
      }
    }

    return $tileMatrix;
  }

  /**
   * Calculates corners of tilematrix
   * @param array $extent
   * @param array $origin
   * @param array $pixel_size
   * @param array $tile_size
   * @return array
   */
  public function tilesOfExtent($extent, $origin, $pixel_size, $tile_size) {
    $tiles = array(
      $this->minsample($extent[0] - $origin[0], $pixel_size[0] * $tile_size[0]),
      $this->minsample($extent[1] - $origin[1], $pixel_size[1] * $tile_size[1]),
      $this->maxsample($extent[2] - $origin[0], $pixel_size[0] * $tile_size[0]),
      $this->maxsample($extent[3] - $origin[1], $pixel_size[1] * $tile_size[1]),
    );
    return $tiles;
  }

  private function minsample($x, $f){
    return $f > 0 ? floor($x / $f) : ceil(($x / $f) - 1);
  }

  private function maxsample($x, $f){
    return $f < 0 ? floor($x / $f) : ceil(($x / $f) - 1);
  }

  /**
   * Default TileMetrixSet for Pseudo Mercator projection 3857
   * @param ?number $maxZoom
   * @return string TileMatrixSet xml
   */
  public function getMercatorTileMatrixSet($maxZoom = 18){
    $denominatorBase = 559082264.0287178;
    $extent = array(-20037508.34,-20037508.34,20037508.34,20037508.34);
    $tileMatrixSet = array();

    for($i = 0; $i <= $maxZoom; $i++){
      $matrixSize = pow(2, $i);
      $tileMatrixSet[] = array(
        'extent' => $extent,
        'id' => (string) $i,
        'matrix_size' => array($matrixSize, $matrixSize),
        'origin' => array($extent[0], $extent[3]),
        'scale_denominator' => $denominatorBase / pow(2, $i),
        'tile_size' => array(256, 256)
      );
    }

    return $this->getTileMatrixSet('GoogleMapsCompatible', $tileMatrixSet, 'EPSG:3857');
  }

  /**
   * Default TileMetrixSet for WGS84 projection 4326
   * @return string Xml
   */
  public function getWGS84TileMatrixSet(){
    $extent = array(-180.000000, -90.000000, 180.000000, 90.000000);
    $scaleDenominators = array(279541132.01435887813568115234, 139770566.00717943906784057617,
      69885283.00358971953392028809, 34942641.50179485976696014404, 17471320.75089742988348007202,
      8735660.37544871494174003601, 4367830.18772435747087001801, 2183915.09386217873543500900,
      1091957.54693108936771750450, 545978.77346554468385875225, 272989.38673277234192937613,
      136494.69336638617096468806, 68247.34668319308548234403, 34123.67334159654274117202,
      17061.83667079825318069197, 8530.91833539912659034599, 4265.45916769956329517299,
      2132.72958384978574031265);
    $tileMatrixSet = array();

    for($i = 0; $i <= 17; $i++){
      $matrixSize = pow(2, $i);
      $tileMatrixSet[] = array(
        'extent' => $extent,
        'id' => (string) $i,
        'matrix_size' => array($matrixSize * 2, $matrixSize),
        'origin' => array($extent[3], $extent[0]),
        'scale_denominator' => $scaleDenominators[$i],
        'tile_size' => array(256, 256)
      );
    }

    return $this->getTileMatrixSet('WGS84', $tileMatrixSet, 'EPSG:4326');
  }

  /**
   * Prints WMTS TileMatrixSet
   * @param string $name
   * @param array $tileMatrixSet Array of levels
   * @param string $crs Code of crs eg: EPSG:3857
   * @return string TileMatrixSet xml
   */
  public function getTileMatrixSet($name, $tileMatrixSet, $crs = 'EPSG:3857'){
    $srs = explode(':', $crs);
    $TileMatrixSet = '<TileMatrixSet>
      <ows:Title>' . $name . '</ows:Title>
      <ows:Abstract>' . $name . ' '. $crs .'</ows:Abstract>
      <ows:Identifier>' . $name . '</ows:Identifier>
      <ows:SupportedCRS>urn:ogc:def:crs:'.$srs[0].'::'.$srs[1].'</ows:SupportedCRS>';
   // <WellKnownScaleSet>urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible</WellKnownScaleSet>;
    foreach($tileMatrixSet as $level){
    $TileMatrixSet .= '
      <TileMatrix>
        <ows:Identifier>' . $level['id'] . '</ows:Identifier>
        <ScaleDenominator>' .  $level['scale_denominator'] . '</ScaleDenominator>
        <TopLeftCorner>'.  $level['origin'][0] . ' ' .  $level['origin'][1] .'</TopLeftCorner>
        <TileWidth>' .  $level['tile_size'][0] . '</TileWidth>
        <TileHeight>' .  $level['tile_size'][1] . '</TileHeight>
        <MatrixWidth>' . $level['matrix_size'][0] . '</MatrixWidth>
        <MatrixHeight>' .  $level['matrix_size'][1] . '</MatrixHeight>
      </TileMatrix>';
    }
    $TileMatrixSet .= '</TileMatrixSet>';

    return $TileMatrixSet;
  }

  /**
   * Returns tilesets getCapabilities
   */
  public function getCapabilities() {

    $layers = array_merge($this->fileLayer, $this->dbLayer);

    //if TileMatrixSet is provided validate it
    for($i = 0; $i < count($layers); $i++){
      if($layers[$i]['profile'] == 'custom'){
        $layers[$i]['tile_matrix'] = $this->parseTileMatrix(
            $layers[$i],
            $layers[$i]['tile_matrix']
        );
      }
    }

    header('Content-type: application/xml');
    echo '<?xml version="1.0" encoding="UTF-8" ?>
<Capabilities xmlns="http://www.opengis.net/wmts/1.0" xmlns:ows="http://www.opengis.net/ows/1.1" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:gml="http://www.opengis.net/gml" xsi:schemaLocation="http://www.opengis.net/wmts/1.0 http://schemas.opengis.net/wmts/1.0/wmtsGetCapabilities_response.xsd" version="1.0.0">
  <!-- Service Identification -->
  <ows:ServiceIdentification>
    <ows:Title>tileserverphp</ows:Title>
    <ows:ServiceType>OGC WMTS</ows:ServiceType>
    <ows:ServiceTypeVersion>1.0.0</ows:ServiceTypeVersion>
  </ows:ServiceIdentification>
  <!-- Operations Metadata -->
  <ows:OperationsMetadata>
    <ows:Operation name="GetCapabilities">
      <ows:DCP>
        <ows:HTTP>
          <ows:Get xlink:href="' . $this->config['protocol'] . '://' . $this->config['baseUrls'][0] . '/wmts/1.0.0/WMTSCapabilities.xml">
            <ows:Constraint name="GetEncoding">
              <ows:AllowedValues>
                <ows:Value>RESTful</ows:Value>
              </ows:AllowedValues>
            </ows:Constraint>
          </ows:Get>
          <!-- add KVP binding in 10.1 -->
          <ows:Get xlink:href="' . $this->config['protocol'] . '://' . $this->config['baseUrls'][0] . '/wmts?">
            <ows:Constraint name="GetEncoding">
              <ows:AllowedValues>
                <ows:Value>KVP</ows:Value>
              </ows:AllowedValues>
            </ows:Constraint>
          </ows:Get>
        </ows:HTTP>
      </ows:DCP>
    </ows:Operation>
    <ows:Operation name="GetTile">
      <ows:DCP>
        <ows:HTTP>
          <ows:Get xlink:href="' . $this->config['protocol'] . '://' . $this->config['baseUrls'][0] . '/wmts/">
            <ows:Constraint name="GetEncoding">
              <ows:AllowedValues>
                <ows:Value>RESTful</ows:Value>
              </ows:AllowedValues>
            </ows:Constraint>
          </ows:Get>
          <ows:Get xlink:href="' . $this->config['protocol'] . '://' . $this->config['baseUrls'][0] . '/wmts?">
            <ows:Constraint name="GetEncoding">
              <ows:AllowedValues>
                <ows:Value>KVP</ows:Value>
              </ows:AllowedValues>
            </ows:Constraint>
          </ows:Get>
        </ows:HTTP>
      </ows:DCP>
    </ows:Operation>
  </ows:OperationsMetadata>
  <Contents>';

    $customtileMatrixSets = '';
    $maxMercatorZoom = 18;

    //layers
    foreach ($layers as $m) {

      $basename = $m['basename'];
      $title = (array_key_exists('name', $m)) ? $m['name'] : $basename;
      $profile = $m['profile'];
      $bounds = $m['bounds'];
      $format = $m['format'] == 'hybrid' ? 'jpgpng' : $m['format'];
      $mime = ($format == 'jpg') ? 'image/jpeg' : 'image/' . $format;

      if ($profile == 'geodetic') {
        $tileMatrixSet = 'WGS84';
      }elseif ($m['profile'] == 'custom') {
        $crs = explode(':', $m['crs']);
        $tileMatrixSet = 'custom' . $crs[1] . $m['basename'];
        $customtileMatrixSets .= $this->getTileMatrixSet(
                $tileMatrixSet,
                $m['tile_matrix'],
                $m['crs']
                );
      } else {
        $tileMatrixSet = 'GoogleMapsCompatible';
        $maxMercatorZoom = max($maxMercatorZoom, $m['maxzoom']);
      }

      $wmtsHost = substr($m['tiles'][0], 0, strpos($m['tiles'][0], $m['basename']));
      $resourceUrlTemplate = $wmtsHost . $basename
              . '/{TileMatrix}/{TileCol}/{TileRow}';
      if(strlen($format) <= 4){
        $resourceUrlTemplate .= '.' . $format;
      }

      echo'
    <Layer>
      <ows:Title>' . $title . '</ows:Title>
      <ows:Identifier>' . $basename . '</ows:Identifier>
      <ows:WGS84BoundingBox crs="urn:ogc:def:crs:OGC:2:84">
        <ows:LowerCorner>' . $bounds[0] . ' ' . $bounds[1] . '</ows:LowerCorner>
        <ows:UpperCorner>' . $bounds[2] . ' ' . $bounds[3] . '</ows:UpperCorner>
      </ows:WGS84BoundingBox>
      <Style isDefault="true">
        <ows:Identifier>default</ows:Identifier>
      </Style>
      <Format>' . $mime . '</Format>
      <TileMatrixSetLink>
        <TileMatrixSet>' . $tileMatrixSet . '</TileMatrixSet>
      </TileMatrixSetLink>
      <ResourceURL format="' . $mime . '" resourceType="tile" template="' . $resourceUrlTemplate . '"/>
    </Layer>';
    }

     // Print custom TileMatrixSets
    if (strlen($customtileMatrixSets) > 0) {
      echo $customtileMatrixSets;
    }

    // Print PseudoMercator TileMatrixSet
    echo $this->getMercatorTileMatrixSet($maxMercatorZoom);

    // Print WGS84 TileMatrixSet
    echo $this->getWGS84TileMatrixSet();

  echo '</Contents>
  <ServiceMetadataURL xlink:href="' . $this->config['protocol'] . '://' . $this->config['baseUrls'][0] . '/wmts/1.0.0/WMTSCapabilities.xml"/>
</Capabilities>';
  }

  /**
   * Returns tile via WMTS specification
   */
  public function getTile() {
    $request = $this->getGlobal('Request');
    if ($request) {
      if (strpos('/', $_GET['Format']) !== false) {
        $format = explode('/', $_GET['Format']);
        $format = $format[1];
      } else {
        $format = $this->getGlobal('Format');
      }
      parent::renderTile(
              $this->getGlobal('Layer'),
              $this->getGlobal('TileMatrix'),
              $this->getGlobal('TileRow'),
              $this->getGlobal('TileCol'),
              $format
              );
    } else {
      parent::renderTile($this->layer, $this->z, $this->y, $this->x, $this->ext);
    }
  }

}

/**
 * Tile map service
 */
class Tms extends Server {

  /**
   * @param array $params
   */
  public $layer;

  /**
   * @var integer
   */
  public $z;

  /**
   * @var integer
   */
  public $y;

  /**
   * @var integer
   */
  public $x;

  /**
   * @var string
   */
  public $ext;

  /**
   *
   * @param array $params
   */
  public function __construct($params) {
    parent::__construct();
    parent::setParams($params);
  }

  /**
   * Returns getCapabilities metadata request
   */
  public function getCapabilities() {
    parent::setDatasets();
    $maps = array_merge($this->fileLayer, $this->dbLayer);
    header('Content-type: application/xml');
    echo'<TileMapService version="1.0.0"><TileMaps>';
    foreach ($maps as $m) {
      $basename = $m['basename'];
      $title = (array_key_exists('name', $m) ) ? $m['name'] : $basename;
      $profile = $m['profile'];
      if ($profile == 'geodetic') {
        $srs = 'EPSG:4326';
      } else {
        $srs = 'EPSG:3857';
      }
      $url = $this->config['protocol'] . '://' . $this->config['baseUrls'][0]
              . '/tms/' . $basename;
      echo '<TileMap title="' . $title . '" srs="' . $srs
        . '" type="InvertedTMS" ' . 'profile="global-' . $profile
        . '" href="' . $url . '" />';
    }
    echo '</TileMaps></TileMapService>';
  }

  /**
   * Prints metadata about layer
   */
  public function getLayerCapabilities() {
    parent::setDatasets();
    $maps = array_merge($this->fileLayer, $this->dbLayer);
    foreach ($maps as $map) {
      if (strpos($map['basename'], $this->layer) !== false) {
        $m = $map;
        break;
      }
    }
    $title = (array_key_exists('name', $m)) ? $m['name'] : $m['basename'];
    $description = (array_key_exists('description', $m)) ? $m['description'] : "";
    $bounds = $m['bounds'];
    if ($m['profile'] == 'geodetic') {
      $srs = 'EPSG:4326';
      $initRes = 0.703125;
    } elseif ($m['profile'] == 'custom') {
      $srs = $m['crs'];
      $bounds = $m['extent'];
      if(isset($m['tile_matrix'][0]['pixel_size'][0])){
        $initRes = $m['tile_matrix'][0]['pixel_size'][0];
      }else{
        $initRes = 1;
      }
    } else {
      $srs = 'EPSG:3857';
      $bounds = array(-20037508.34,-20037508.34,20037508.34,20037508.34);
      $initRes = 156543.03392804062;
    }
    $mime = ($m['format'] == 'jpg') ? 'image/jpeg' : 'image/png';
    header("Content-type: application/xml");
    $serviceUrl = $this->config['protocol'] . '://' . $this->config['baseUrls'][0] . '/' . $m['basename'];
    echo '<TileMap version="1.0.0" tilemapservice="' . $serviceUrl . '" type="InvertedTMS">
  <Title>' . htmlspecialchars($title) . '</Title>
  <Abstract>' . htmlspecialchars($description) . '</Abstract>
  <SRS>' . $srs . '</SRS>
  <BoundingBox minx="' . $bounds[0] . '" miny="' . $bounds[1] . '" maxx="' . $bounds[2] . '" maxy="' . $bounds[3] . '" />
  <Origin x="' . $bounds[0] . '" y="' . $bounds[1] . '"/>
  <TileFormat width="256" height="256" mime-type="' . $mime . '" extension="' . $m['format'] . '"/>
  <TileSets profile="global-' . $m['profile'] . '">';
    for ($zoom = $m['minzoom']; $zoom < $m['maxzoom'] + 1; $zoom++) {
      $res = $initRes / pow(2, $zoom);
      $url = $this->config['protocol'] . '://' . $this->config['baseUrls'][0] . '/' . $m['basename'] . '/' . $zoom;
      echo '<TileSet href="' . $url . '" units-per-pixel="' . $res . '" order="' . $zoom . '" />';
    }
    echo'</TileSets></TileMap>';
  }

  /**
   * Process getTile request
   */
  public function getTile() {
    parent::renderTile($this->layer, $this->z, $this->y, $this->x, $this->ext);
  }
}

/**
 * Simple router
 */
class Router {

  /**
   * @param array $routes
   */
  public static function serve($routes) {
    $path_info = '/';
	global $config;
	$xForwarded = false;
	if (isset($_SERVER['HTTP_X_FORWARDED_PROTO'])) {
		if ($_SERVER['HTTP_X_FORWARDED_PROTO'] == 'https') {
			$xForwarded = true;
		}
	}
	$config['protocol'] = ((isset($_SERVER['HTTPS']) or (isset($_SERVER['SERVER_PORT']) && $_SERVER['SERVER_PORT'] == 443)) or $xForwarded) ? 'https' : 'http';
    if (!empty($_SERVER['PATH_INFO'])) {
      $path_info = $_SERVER['PATH_INFO'];
    } else if (!empty($_SERVER['ORIG_PATH_INFO']) && strpos($_SERVER['ORIG_PATH_INFO'], 'tileserver.php') === false) {
      $path_info = $_SERVER['ORIG_PATH_INFO'];
    } else if (!empty($_SERVER['REQUEST_URI']) && strpos($_SERVER['REQUEST_URI'], '/tileserver.php') !== false) {
      $path_info = $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI'];
      $config['baseUrls'][0] = $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI'] . '?';
    } else {
      if (!empty($_SERVER['REQUEST_URI'])) {
        $path_info = (strpos($_SERVER['REQUEST_URI'], '?') > 0) ? strstr($_SERVER['REQUEST_URI'], '?', true) : $_SERVER['REQUEST_URI'];
      }
    }
    $discovered_handler = null;
    $regex_matches = array();

    if ($routes) {
      $tokens = array(
          ':string' => '([a-zA-Z]+)',
          ':number' => '([0-9]+)',
          ':alpha' => '([a-zA-Z0-9-_@\.]+)'
      );
      //global $config;
      foreach ($routes as $pattern => $handler_name) {
        $pattern = strtr($pattern, $tokens);
        if (preg_match('#/?' . $pattern . '/?$#', $path_info, $matches)) {
          if (!isset($config['baseUrls'])) {
            $config['baseUrls'][0] = $_SERVER['HTTP_HOST'] . preg_replace('#/?' . $pattern . '/?$#', '', $path_info);
          }
          $discovered_handler = $handler_name;
          $regex_matches = $matches;
          break;
        }
      }
    }
    $handler_instance = null;
    if ($discovered_handler) {
      if (is_string($discovered_handler)) {
        if (strpos($discovered_handler, ':') !== false) {
          $discoverered_class = explode(':', $discovered_handler);
          $discoverered_method = explode(':', $discovered_handler);
          $handler_instance = new $discoverered_class[0]($regex_matches);
          call_user_func(array($handler_instance, $discoverered_method[1]));
        } else {
          $handler_instance = new $discovered_handler($regex_matches);
        }
      } elseif (is_callable($discovered_handler)) {
        $handler_instance = $discovered_handler();
      }
    } else {
      if (!isset($config['baseUrls'][0])) {
        $config['baseUrls'][0] = $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI'];
      }
      if (strpos($_SERVER['REQUEST_URI'], '=') != false) {
        $kvp = explode('=', $_SERVER['REQUEST_URI']);
        $_GET['callback'] = $kvp[1];
        $params[0] = 'index';
        $handler_instance = new Json($params);
        $handler_instance->getJson();
      }
      $handler_instance = new Server;
      $handler_instance->getHtml();
    }
  }

}
