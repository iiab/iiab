var files = <?php $out = array();
foreach (glob('/library/www/osm-vector-maps.tiles/*') as $filename) {
    $p = pathinfo($filenae);
    $out[] = $p['filename'];
}
echo json_encode($out); ?>;
