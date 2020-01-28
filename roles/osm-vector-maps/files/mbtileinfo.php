<?php
global $config;
$config['serverTitle'] = 'Maps hosted with TileServer-php v2.0';
$config['availableFormats'] = array('png', 'jpg', 'jpeg', 'gif', 'webp', 'pbf', 'hybrid');
$config['dataRoot'] = '/library/www/osm-vector-maps/viewer/tiles/';
$config['baseUrls'] = array('');
$config['protocol'] = 'http';

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
      echo('Failed of open PDO with string: sqlite:' . $tileset).'<br>\n';
      echo $exc->getTraceAsString();
      die;
    }

    if (!isset($this->db)) {
      header('Content-type: text/plain');
      echo 'Incorrect tileset name: ' . $tileset;
      die;
    }
  }
}

$ts = new Server();
//$ts->metadataFromMbtiles($_REQUEST['file']);
$ts->setDatasets();
$maps = $ts->dbLayer;
$meta = array();
foreach ($maps as $map){
   $data = array();
   $data['basename'] = $map['basename'];
   $data['bounds'] = $map['bounds'];
   $data['maxzoom'] = $map['maxzoom'];
   $data['minzoom'] = $map['minzoom'];
   $meta[] = $data;
}
echo(json_encode($meta));
?>
