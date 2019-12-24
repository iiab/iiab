<?php
$db = new SQLite3('cities1000.sqlite');
if (isset($_REQUEST['query'])) {
   $searchfor = $_REQUEST['query'];
   $sql = "select geonameid,name,latitude,longitude,population,country_code from features where name like '" . $searchfor . "%' order by population desc limit 10;";
} else {
   $sql = "select geonameid,name,latitude,longitude,population,country_code from features  order by population desc limit 10;";
}
$results = $db->query($sql);

$list = array();
while ($row = $results->fetchArray()) {
	$dict = array();
	$dict["name"] = $row["name"];
        $dict["country_code"] = $row["country_code"];
	$dict["latitude"] = $row["latitude"];
	$dict["longitude"] = $row["longitude"];
	$dict["population"] = $row["population"];
	$dict["geonameid"] = $row["geonameid"];
	array_push($list,$dict);
}
$json = json_encode($list);
print_r($json);

?>
