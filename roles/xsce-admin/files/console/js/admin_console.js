// admin_console.js
// copyright 2016 Tim Moody

var today = new Date();
var dayInMs = 1000*60*60*24;

var xsceContrDir = "/etc/xsce/";
var consoleJsonDir = "/common/assets/";
var xsceCmdService = "cmd-service.php";
var ansibleFacts = {};
var ansibleTagsStr = "";
var effective_vars = {};
var config_vars = {};
var xsce_ini = {};
var job_status = {};
var langCodes = {}; // iso code, local name and English name for all languages we support, read from file
var zimCatalog = {}; // working composite catalog of kiwix, installed, and wip zims
var zimLangs = {}; // working list of iso codes in zimCatalog
var zimGroups = {}; // zim ids grouped by language and category
var kiwixCatalog = {}; // catalog of kiwix zims, read from file downloaded from kiwix.org
var kiwixCatalogDate = new Date; // date of download, stored in json file
var installedZimCat = {}; // catalog of installed, and wip zims
var rachelStat = {}; // installed, enabled and whether content is installed and which is enabled

var zimsInstalled = []; // list of zims already installed
var zimsScheduled = []; // list of zims being installed (wip)

var downloadedFiles = {};

var langNames = []; // iso code, local name and English name for languages for which we have zims sorted by English name for language
var topNames = ["ara","eng","spa","fra","hin","por"]; // languages for top language menu
var defaultLang = "eng";
var langGroups = {"en":"eng"}; // language codes to treat as a single code
var selectedLangs = []; // languages selected by gui for display of content
var selectedZims = [];
var sysStorage = {};
sysStorage.root = {};
sysStorage.library = {};
sysStorage.library.partition = false; // no separate library partition
sysStorage.zims_selected_size = 0;

// because jquery does not percolate .fail conditions in async chains
// and because an error returned from the server is not an ajax error
// flag must be set to false before use

// defaults for ip addr of server and other info returned from server-info.php
var serverInfo = {"xsce_server_ip":"","xsce_client_ip":"","xsce_server_found":"TRUE","xsce_cmdsrv_running":"FALSE"};
var initStat = {};

// MAIN ()

function main() {

// Set jquery ajax calls not to cache in browser
  $.ajaxSetup({ cache: false });

// declare generic ajax error handler called by all .fail events
 $( document ).ajaxError(ajaxErrhandler);

// get default help
  getHelp("Overview.rst");

  //navButtonsEvents(); - now done after successful init

  initStat["active"] = false;
  initStat["error"] = false;
  initStat["alerted"] = {};

// Get Ansible facts and other data
  init();
}

// Set up nav

function navButtonsEvents() {
  $("ul.nav a").click(function (e) {
    e.preventDefault();
    $(this).tab('show');
    console.log($(this));
    if ($(this).is('[call-after]')) {
      //if ($this).attr('call-after') !== undefined) {
      console.log($(this).attr('call-after'));
      if ($(this).is('[call-after-arg]'))
      {
        console.log($(this).attr('call-after-arg'));
        window[$(this).attr('call-after')]($(this).attr('call-after-arg'));
      }
      else
        window[$(this).attr('call-after')]();
    }
    else
      console.log(' no call-after');
  });
}

// BUTTONS

// Control Buttons

function controlButtonsEvents() {
  $("#REBOOT").click(function(){
    rebootServer();
  });

  $("#POWEROFF").click(function(){
    poweroffServer();
  });
  console.log(' REBOOT and POWEROFF set');
}

  // Configuration Buttons

function configButtonsEvents() {
  $("#Bad-CMD").click(function(){
    sendCmdSrvCmd("XXX", testCmdHandler);
  });

  $("#Test-CMD").click(function(){
    //sendCmdSrvCmd("TEST ;", testCmdHandler);
    getJobStat();
  });

  $("#List-CMD").click(function(){
  	// xsce-cmdsrv-ctl LIST-LIBR '{"sub_dir":"downloads/zims"}'
    sendCmdSrvCmd("LIST", listCmdHandler);
  });

  $("#SET-CONF-CMD").click(function(){
    make_button_disabled("#SET-CONF-CMD", true);
    setConfigVars();
    make_button_disabled("#SET-CONF-CMD",false);
  });

  $("#SAVE-WHITELIST").click(function(){
    make_button_disabled("#SAVE-WHITELIST", true);
    setWhitelist();
    make_button_disabled("#SAVE-WHITELIST", false);
  });

  $("#RUN-ANSIBLE").click(function(){
    make_button_disabled("#RUN-ANSIBLE", true);
    runAnsible("ALL-TAGS");
    //runAnsible("addons");
    make_button_disabled("#RUN-ANSIBLE", false);
  });

  $("#RESET-NETWORK").click(function(){
    make_button_disabled("#RESET-NETWORK", true);
    resetNetwork();
    //runAnsible("addons");
    make_button_disabled("#RESET-NETWORK", false);
  });

  $("#RUN-TAGS").click(function(){
    make_button_disabled("#RUN-TAGS", true);
    var tagList = "";
    $('#ansibleTags input').each( function(){
      if (this.type == "checkbox") {
        if (this.checked)
        tagList += this.name + ',';
      }
    });
    if (tagList.length > 0)
    tagList = tagList.substring(0, tagList.length - 1);
    runAnsible(tagList);
    //runAnsible("addons");
    make_button_disabled("#RUN-TAGS", false);
  });

  $("#STOP").click(function(){
    sendCmdSrvCmd("STOP", genericCmdHandler);
  });
}

  // Install Content Buttons

function instContentButtonsEvents() {
  $("#selectLangButton").click(function(){
    procZimGroups();
    $('#selectLangCodes').modal('hide');
    $('#ZimLanguages2').hide();
    procZimLangs(); // make top menu reflect selections
  });

  $("#selectLangButton2").click(function(){
    procZimGroups();
    $('#selectLangCodes').modal('hide');
    $('#ZimLanguages2').hide();
    procZimLangs(); // make top menu reflect selections
  });

  $("#moreLangButton").click(function(){
    $('#ZimLanguages2').show();
  });

  $("#INST-ZIMS").click(function(){
    var zim_id;
    make_button_disabled("#INST-ZIMS", true);

    $('#ZimDownload input').each( function(){
      if (this.type == "checkbox")
      if (this.checked){
        zim_id = this.name;
        if (zimsInstalled.indexOf(zim_id) == -1 && zimsScheduled.indexOf(zim_id) == -1)
        instZim(zim_id);
      }
    });
    procZimGroups();
    alert ("Selected Zims scheduled to be installed.\n\nPlease view Utilities->Display Job Status to see the results.");
    make_button_disabled("#INST-ZIMS", false);
  });

  $("#launchKaliteButton").click(function(){
    var url = "http://" + window.location.host + ":8008";
    //consoleLog(url);
    window.open(url);
  });

  $("#ZIM-STATUS-REFRESH").click(function(){
    refreshZimStat();
  });

  $("#RESTART-KIWIX").click(function(){
    restartKiwix();
  });

  $("#KIWIX-LIB-REFRESH").click(function(){
    getKiwixCatalog();
  });

  $("#DOWNLOAD-RACHEL").click(function(){
  	if (rachelStat.content_installed == true){
  	  var rc = confirm("RACHEL content is already in the library.  Are you sure you want to download again?");
  	  if (rc != true)
  	    return;
  	}
    sendCmdSrvCmd("INST-RACHEL", genericCmdHandler, "DOWNLOAD-RACHEL");
    alert ("RACHEL scheduled to be downloaded and installed.\n\nPlease view Utilities->Display Job Status to see the results.");
  });

  $("#DEL-DOWNLOADS").click(function(){
  	var r = confirm("Press OK to Delete Checked Files");
    if (r != true)
      return;
  	make_button_disabled("#DEL-DOWNLOADS", true);
    delDownloadedFiles();
    make_button_disabled("#DEL-DOWNLOADS", false);
  });
}

  // Util Buttons

function utilButtonsEvents() {
  $("#CHGPW").click(function(){
  	changePassword();
  });

  $("#JOB-STATUS-REFRESH").click(function(){
  	make_button_disabled("#JOB-STATUS-REFRESH", true);
    getJobStat();
    make_button_disabled("#JOB-STATUS-REFRESH", false);
  });

  $("#CANCEL-JOBS").click(function(){
  	var cmdList = [];
    make_button_disabled("#CANCEL-JOBS", true);
    $('#jobStatTable input').each( function(){
      if (this.type == "checkbox")
        if (this.checked){
          var job_idArr = this.id.split('-');
          job_id = job_idArr[1];

          // cancelJobFunc returns the function to call not the result as needed by array.push()
          cmdList.push(cancelJobFunc(job_id));
          if (job_status[job_id]["cmd_verb"] == "INST-ZIMS"){
          	var zim_id = job_status[job_id]["cmd_args"]["zim_id"];
          	//consoleLog (zim_id);
            if (zimsScheduled.indexOf(zim_id) > -1){
              zimsScheduled.pop(zim_id);
              updateZimDiskSpaceUtil(zim_id, false)
              procZimGroups();
              //$( "input[name*='" + zim_id + "']" ).checked = false;
            }
          }
          this.checked = false;
        }
    });
    //consoleLog(cmdList);
    $.when.apply($, cmdList).then(getJobStat, procZimCatalog);
    alert ("Jobs marked for Cancellation.\n\nPlease click Refresh to see the results.");
    make_button_disabled("#CANCEL-JOBS", false);
  });

  $("#GET-INET-SPEED").click(function(){
    getInetSpeed();
  });

  $("#GET-INET-SPEED2").click(function(){
    getInetSpeed2();
  });
}

function configFieldsEvents() {

  // Static Wan Fields

  $("#gui_static_wan").change(function(){
    gui_static_wanVal();
  });

  $("#gui_static_wan_ip").on('blur', function(){
    staticIpVal("#gui_static_wan_ip");
  });

  $("#gui_static_wan_netmask").on('blur', function(){
    staticIpVal("#gui_static_wan_netmask");
  });

  $("#gui_static_wan_gateway").on('blur', function(){
    staticIpVal("#gui_static_wan_gateway");
  });

  $("#gui_static_wan_nameserver").on('blur', function(){
    staticIpVal("#gui_static_wan_nameserver");
  });
}

function make_button_disabled(id, grey_out) {
	// true means grey out the button and disable, false means the opposite
  if (grey_out){
  	$(id).prop('disabled', true);
    $(id).css({opacity:".5"});
  }
  else {
  	$(id).css({opacity:"1"});
    $(id).prop('disabled', false);
  }
}

// Field Validations

function xsce_hostnameVal()
{
  //alert ("in xsce_hostnameVal");
  var xsce_hostname = $("#xsce_hostname").val();
  consoleLog(xsce_hostname);
  if (xsce_hostname == ""){
    alert ("Host Name can not be blank.");
    $("#xsce_hostname").val(config_vars['xsce_hostname'])
    setTimeout(function () {
      $("#xsce_hostname").focus(); // hack for IE
    }, 100);
    return false;
  }
  // regex must match to be valid
  //var hostRegex = new RegExp("^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*))$");
  var hostRegex = /^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*))$/;
  if (! hostRegex.test(xsce_hostname)) {
    alert ("Host Name can only have letters, numbers, and dashes and may not start with a dash.");
    //$("#xsce_hostname").val(config_vars['xsce_domain'])
    setTimeout(function () {
      $("#xsce_hostname").focus(); // hack for IE
    }, 100);
    return false
  }

  return true;
}

function xsce_domainVal()
{
  //alert ("in xsce_domainVal");
  var xsce_domain = $("#xsce_domain").val();
  consoleLog(xsce_domain);
  if (xsce_domain == ""){
    alert ("Domain Name can not be blank.");
    $("#xsce_domain").val(config_vars['xsce_domain'])
    setTimeout(function () {
      $("#xsce_domain").focus(); // hack for IE
    }, 100);
    return false;
  }
  // any regex match is invalid
  var domainRegex = /^[\.\-]|[\.\-]$|[^\.a-zA-Z0-9-]/;
  if (domainRegex.test(xsce_domain)) {
    alert ("Domain Name can only have letters, numbers, dashes, and dots and may not have a dot or dash at beginning or end.");
    //$("#xsce_domain").val(config_vars['xsce_domain'])
    setTimeout(function () {
      $("#xsce_domain").focus(); // hack for IE
    }, 100);
    return false
  }

  return true;
}
function gui_static_wanVal()
{
  // we come here if the checkbox was clicked
  // if it is now checked then it is newly so and we assign defaults

  // alert ("in gui_static_wanVal");

  if ($("#gui_static_wan").prop('checked')){
    staticIpDefaults ();
  }
}

function staticIpDefaults () {
	if(typeof ansibleFacts.ansible_default_ipv4.address === 'undefined'){
		$("#gui_static_wan_ip").val("127.0.0.1");
    $("#gui_static_wan_netmask").val("255.255.255.0");
    $("#gui_static_wan_gateway").val("127.0.0.1");
    $("#gui_static_wan_nameserver").val("127.0.0.1");
  }
  else {
    $("#gui_static_wan_ip").val(ansibleFacts.ansible_default_ipv4.address);
    $("#gui_static_wan_netmask").val(ansibleFacts.ansible_default_ipv4.netmask);
    $("#gui_static_wan_gateway").val(ansibleFacts.ansible_default_ipv4.gateway);
    $("#gui_static_wan_nameserver").val(ansibleFacts.ansible_default_ipv4.gateway);
  }
}

function staticIpVal(fieldId) {
    //Check Format
    var fieldVal = $(fieldId).val();
    var ip = fieldVal.split(".");
    var valid = true;

    if (ip.length != 4) {
        valid = false;
    }

    //Check Numbers
    for (var c = 0; c < 4; c++) {
        //Perform Test
        if ( ip[c] <= -1 || ip[c] > 255 ||
             isNaN(parseFloat(ip[c])) ||
             !isFinite(ip[c])  ||
             ip[c].indexOf(" ") !== -1 ) {

             valid = false;
        }
    }
    if (valid == false){
    	alert ("Invalid: Field must be N.N.N.N where N is a number between 0 and 255");
      setTimeout(function () {
        $(fieldId).focus(); // hack for IE
      }, 100);
      return false;
    }
    else
      return true;
}

//var testCmdHandler = function (data, textStatus, jqXHR) is not necessary
var testCmdHandler = function (data)
//function testCmdHandler (data)
{
  //alert ("in Cmdhandler");
  consoleLog(data);
  return true;
};

function listCmdHandler (data)
{
  //alert ("in listCmdHandler");
  consoleLog(data);
  //consoleLog(jqXHR);
  return true;
}

function genericCmdHandler (data)
{
  //alert ("in genericCmdHandler");
  consoleLog(data);
  //consoleLog(jqXHR);
  return true;
}

function getAnsibleFacts (data)
{
  //alert ("in getAnsibleFacts");
  consoleLog(data);
  ansibleFacts = data;
  var jstr = JSON.stringify(ansibleFacts, undefined, 2);
  var html = jstr.replace(/\n/g, "<br>").replace(/[ ]/g, "&nbsp;");
  $( "#ansibleFacts" ).html(html);
  //consoleLog(jqXHR);
  return true;
}

function getAnsibleTags (data)
{
  //alert ("in getAnsibleTags");
  consoleLog(data);
  ansibleTagsStr = data['ansible_tags'];
  ansibleTagsArr = ansibleTagsStr.split(',');
  var html = '<table width="80%"><tr>';
  var j = 0;
  for (var i in ansibleTagsArr){
    html += '<td width="20%"><label><input type="checkbox" name="' + ansibleTagsArr[i] + '">' + ansibleTagsArr[i] + '</label></td>';
    if (j++ == 4){
      html += '</tr><tr>';
      j = 0;
    }
  }
  html += "</tr></table>";
  //consoleLog(html);
  //jstr = JSON.stringify(ansibleFacts, undefined, 2);
  //html = jstr.replace(/\n/g, "<br>").replace(/[ ]/g, "&nbsp;");
  $( "#ansibleTags" ).html(html);
  //consoleLog(jqXHR);
  return true;
}

function getInstallVars (data)
{
  //alert ("in getInstallVars");
  consoleLog(data);
  effective_vars = data;
  //consoleLog(jqXHR);
  return true;
}
function getConfigVars (data)
{
  //alert ("in getConfigVars");
  consoleLog(data);
  config_vars = data;
  return true;
}

function assignConfigVars (data)
{
  // If config_vars has a value use it
  // Otherwise if effective_vars has a value use it
  $('#Configure input').each( function(){
    if (config_vars.hasOwnProperty(this.name)){
      var prop_val = config_vars[this.name];
      //consoleLog(this.name + "using config_vars");
    }
    else if (effective_vars.hasOwnProperty(this.name)){
      prop_val = effective_vars[this.name];
      config_vars[this.name] = effective_vars[this.name];
      //consoleLog(this.name + "using effective_vars");
    }
    else{
      if (this.type == "checkbox")
      prop_val = false;
      if (this.type == "text")
      prop_val = "";
      if (this.type == "radio")
      prop_val = "";
    }
    if (this.type == "checkbox"){
      $(this).prop('checked', config_vars[this.name]);
      var service = this.name.split("_enabled")[0];
      var service_install = service + "_install";
      var service_id = "." + service + "_service";
      if (effective_vars.hasOwnProperty(service_install)){
      	if (effective_vars[service_install])
      	  $(service_id).show();
      	else
      	  $(service_id).hide();
      }
    }
    if (this.type == "text")
    this.value = config_vars[this.name];
    if (this.type == "radio"){
      // this will get called once for each button, but should only check one of the set
      setRadioButton(this.name, config_vars[this.name]);
    }
    //console.log($(this).val());
    //consoleLog(this.name);
  });

  //config_vars = data;
  //consoleLog(jqXHR);
  //initConfigVars()
  return true;
}

function setRadioButton(name, value){
  // id must follow the convention name-value
  var field_id = "#" + name + "-" + value;
  //consoleLog(field_id);
  $(field_id).prop('checked', true);
}

function initConfigVars()
{
  if ($.isEmptyObject(ansibleFacts)
      || $.isEmptyObject(xsce_ini)
      || $.isEmptyObject(effective_vars)
      // || $.isEmptyObject(config_vars) is empty the first time
      ){
      consoleLog("initConfigVars found empty data");
      displayServerCommandStatus ("initConfigVars found empty data")
      return;
    }
  // handle exception where gui name distinct and no data
  // home page - / added when used in ansible
  if (! config_vars.hasOwnProperty('gui_desired_home_url')){
  	config_vars['gui_desired_home_url'] = "home";
  	consoleLog("home url is " + config_vars['gui_desired_home_url']);
  }
  assignConfigVars();
  var html = "Gateway: ";
  if(typeof ansibleFacts.ansible_default_ipv4.address === 'undefined'){
    html += "Not Found<BR>";
    $("#gui_static_wan").prop('checked', false);
  }
  else {
    html += "Found<BR>";
    html += "WAN: " + ansibleFacts.ansible_default_ipv4.address + " on " + ansibleFacts.ansible_default_ipv4.alias + "<BR>";
  }
  //consoleLog(config_vars);
  html += "LAN: on " + xsce_ini.network.computed_lan  + "<BR>";
  html += "Network Mode: " + xsce_ini.network.xsce_network_mode + "<BR>";
  $("#discoveredNetwork").html(html);
  if (typeof config_vars.gui_desired_network_role === "undefined")
  setRadioButton("gui_desired_network_role", xsce_ini.network.xsce_network_mode)
  initStaticWanVars();
}

function initStaticWanVars() {
	// if use static wan is checked they are assumed to be valid
	if ($("#gui_static_wan").prop('checked') == false){
    staticIpDefaults ();
  }
}

function setConfigVars ()
{
  var cmd_args = {}
  //alert ("in setConfigVars");
  $('#Configure input').each( function(){
    if (this.type == "checkbox") {
      if (this.checked)
      config_vars[this.name] = true; // must be true not True
      else
        config_vars[this.name] = false;
      }
      if (this.type == "text")
      config_vars[this.name] = $(this).val();
      if (this.type == "radio"){
        fieldName = this.name;
        fieldName = "input[name=" + this.name + "]:checked"
        //consoleLog(fieldName);
        config_vars[this.name] = $(fieldName).val();
      }
    });
    cmd_args['config_vars'] = config_vars;
    var cmd = "SET-CONF " + JSON.stringify(cmd_args);
    sendCmdSrvCmd(cmd, genericCmdHandler);
    alert ("Saving Configuration.");
    return true;
  }

function changePassword ()
{
	if ($("#xsce_admin_new_password").val() != $("#xsce_admin_new_password2").val()){
    	alert ("Invalid: New Password and Repeat New Password do NOT Match.");
      setTimeout(function () {
        $("#xsce_admin_new_password").focus(); // hack for IE
      }, 100);
      return false;
    }

  var cmd_args = {}
  cmd_args['user'] = $("#xsce_admin_user").val();
  cmd_args['oldpasswd'] = $("#xsce_admin_old_password").val();
  cmd_args['newpasswd'] = $("#xsce_admin_new_password").val();

  var cmd = "CHGPW " + JSON.stringify(cmd_args);
  sendCmdSrvCmd(cmd, changePasswordSuccess, "CHGPW");
  //alert ("Changing Password.");
  return true;
}

function changePasswordSuccess ()
{
  alert ("Password Changed.");
  return true;
}
  function getXsceIni ()
  {
    //alert ("in getXsceIni");
    sendCmdSrvCmd("GET-XSCE-INI", procXsceIni);
    return true;
  }

  function procXsceIni (data)
  {
    //alert ("in procXsceIni");
    consoleLog(data);
    xsce_ini = data;
    var jstr = JSON.stringify(xsce_ini, undefined, 2);
    var html = jstr.replace(/\n/g, "<br>").replace(/[ ]/g, "&nbsp;");
    $( "#xsceIni" ).html(html);
    //consoleLog(jqXHR);

    // Set Password Fields
    $( "#xsce_admin_user").val(xsce_ini['xsce-admin']['xsce_admin_user']);
    return true;
  }
  function getWhitelist (data)
  {
    //alert ("in getWhitelist");
    //consoleLog(data);
    var whlist_array = data['xsce_whitelist'];
    var whlist_str = whlist_array[0];
    for (var i = 1; i < whlist_array.length; i++) {
      whlist_str += '\n' + whlist_array[i];
    }
    //$('#xsce_whitelist').val(data['xsce_whitelist']);
    $('#xsce_whitelist').val(whlist_str);
    return true;
  }

  function setWhitelist ()
  {
    //consoleLog ("in setWhitelist");
    var whlist_ret = {}
    var whlist_array = $('#xsce_whitelist').val().split('\n');
    whlist_ret['xsce_whitelist'] = whlist_array;
    var cmd = "SET-WHLIST " + JSON.stringify(whlist_ret);
    //consoleLog(cmd);
    sendCmdSrvCmd(cmd, genericCmdHandler);
    alert ("Saving Permitted URLs List.");
    return true;
  }

  function runAnsible (tags)
  {
    var command = formCommand("RUN-ANSIBLE", "tags", tags);
    //alert ("in runAnsible");
    consoleLog(command);
    sendCmdSrvCmd(command, genericCmdHandler);
    alert ("Scheduling Ansible Run.");
    return true;
  }

  function resetNetwork ()
  {
    var command = "RESET-NETWORK";
    //alert ("in resetNetwork");
    consoleLog(command);
    sendCmdSrvCmd(command, genericCmdHandler);
    alert ("Scheduling Network Reset.");
    return true;
  }

  // Install Content functions

  function instZim(zim_id)
  {
    zimsScheduled.push(zim_id);
    var command = "INST-ZIMS"
    var cmd_args = {}
    cmd_args['zim_id'] = zim_id;
    cmd = command + " " + JSON.stringify(cmd_args);
    sendCmdSrvCmd(cmd, genericCmdHandler, "", instZimError, cmd_args);
    return true;
  }

  function instZimError(data, cmd_args)
  {
    consoleLog(cmd_args);
    //cmdargs = JSON.parse(command);
    //consoleLog(cmdargs);
    consoleLog(cmd_args["zim_id"]);
    zimsScheduled.pop(cmd_args["zim_id"]);
    procZimGroups();
    return true;
  }

  function restartKiwix() // Restart Kiwix Server
  {
    var command = "RESTART-KIWIX";
    sendCmdSrvCmd(command, genericCmdHandler);
    alert ("Restarting Kiwix Server.");
    return true;
  }

  function getKiwixCatalog() // Downloads kiwix catalog from kiwix
  {
    make_button_disabled("#KIWIX-LIB-REFRESH", true);
    // remove any selections as catalog may have changed
    selectedZims = [];

    var command = "GET-KIWIX-CAT";
    sendCmdSrvCmd(command, procKiwixCatalog, "KIWIX-LIB-REFRESH");
    return true;
  }

  function refreshZimStat(){
  	// Retrieve installed and wip zims and refresh screen
    // Remove any unprocessed selections
    selectedZims = [];

    $.when(getSpaceAvail(), getZimStat()).then(procDiskSpace);
    return true;
  }

  function getZimStat(){
    return sendCmdSrvCmd("GET-ZIM-STAT", procZimStatInit);
  }

  function procKiwixCatalog() {
    $.when(
      getZimStat(),
      readKiwixCatalog()
    )
    .done(function() {
      procZimCatalog();
      sumCheckedZimDiskSpace();
      setZimDiskSpace();
    })
    .always(function() {
      alert ("Kiwix Catalog has been downloaded.");
      make_button_disabled("#KIWIX-LIB-REFRESH", false);
    })
  }

  function procZimStatInit(data) {
    installedZimCat = data;
  }

  function procZimStat(data) {
    installedZimCat = data;
    procZimCatalog();
    procDiskSpace();
  }

  function procZimLangs() {
    //consoleLog (zimLangs);
    var html = '';
    var topHtml = '';
    var bottomHtml = '';
    for (var i in langNames){
      html = '<span class="lang-codes"><label><input type="checkbox" name="' + langNames[i].code + '"';
      if (selectedLangs.indexOf(langNames[i].code) != -1)
      html += ' checked';
      html += '>&nbsp;&nbsp;<span>' + langNames[i].locname + '</span><span> (' + langNames[i].engname + ') [' + langNames[i].code + ']</span></label></span>';

      if (topNames.indexOf(langNames[i].code) >= 0 || selectedLangs.indexOf(langNames[i].code) != -1) {
        topHtml += html;
      }
      else {
        bottomHtml += html;
      }
    }
    $( "#ZimLanguages" ).html(topHtml);
    $( "#ZimLanguages2" ).html(bottomHtml);
  }

function procZimGroups() {
  // get list of selected langcodes
  selectedLangs = [];
  $('#selectLangCodes input').each( function(){
    if (this.checked) {
      selectedLangs.push(this.name);
    }
  });
  var html = "<br>";
  $.each(selectedLangs, function(index, lang) {
    //consoleLog(index);
    if (lang in zimGroups){
      //consoleLog (lang);
      html += "<h2>" + langCodes[lang]['locname'] + ' (' + langCodes[lang]['engname'] + ")</h2>";
      $.each(zimGroups[lang], function(key, zimList) {
        html += "<h3>" + key + "</h3>";
        $.each(zimList, function(key, zimId) {
          var zim = zimCatalog[zimId];
          var colorClass = "";
          var colorClass2 = "";
          if (zimsInstalled.indexOf(zimId) >= 0){
            colorClass = "installed";
            colorClass2 = 'class="installed"';
          }
          if (zimsScheduled.indexOf(zimId) >= 0){
            colorClass = "scheduled";
            colorClass2 = 'class="scheduled"';
          }
          html += '<label ';
          html += '><input type="checkbox" name="' + zimId + '"';
          //html += '><img src="images/' + zimId + '.png' + '"><input type="checkbox" name="' + zimId + '"';
          if ((zimsInstalled.indexOf(zimId) >= 0) || (zimsScheduled.indexOf(zimId) >= 0))
          html += 'disabled="disabled" checked="checked"';
          html += 'onChange="updateZimDiskSpace(this)"></label>'; // end input
          var zimDesc = zim.title + ' (' + zim.description + ') [' + zim.perma_ref + ']';
          html += '<span class="zim-desc ' + colorClass + '" >&nbsp;&nbsp;' + zimDesc + '</span>';
          html += '<span ' + colorClass2 + 'style="display:inline-block; width:120px;"> Date: ' + zim.date + '</span>';
          html += '<span ' + colorClass2 +'> Size: ' + readableSize(zim.size);
          if (zimsInstalled.indexOf(zimId) >= 0)
          html += ' - INSTALLED';
          if (zimsScheduled.indexOf(zimId) >= 0)
          html += ' - WORKING ON IT';
          html += '</span><BR>';
        });
      });
    }
  });
  //consoleLog (html);
  $( "#ZimDownload" ).html(html);
}

function getLangCodes() {
  //alert ("in sendCmdSrvCmd(");
  //consoleLog ('ran sendCmdSrvCmd');
  //if (asyncFlag === undefined) asyncFlag = false;

  var resp = $.ajax({
    type: 'GET',
    url: consoleJsonDir + 'lang_codes.json',
    dataType: 'json'
  })
  .done(function( data ) {
    langCodes = data;
    consoleLog(langCodes);
  })
  .fail(jsonErrhandler);

  return resp;
}

function readKiwixCatalog() { // Reads kiwix catalog from file system as json
  //consoleLog ("in readKiwixCatalog");
  //consoleLog ('ran sendCmdSrvCmd');
  //if (asyncFlag === undefined) asyncFlag = false;

  var resp = $.ajax({
    type: 'GET',
    url: consoleJsonDir + 'kiwix_catalog.json',
    dataType: 'json'
  })
  .done(function( data ) {
  	kiwixCatalogDate = Date.parse(data['download_date']);
  	kiwixCatalog = data['zims'];
    //consoleLog(kiwixCatalog);
  })
  .fail(jsonErrhandler);

  return resp;
}

function checkKiwixCatalogDate() {
	today = new Date();
	if (today - kiwixCatalogDate > 30 * dayInMs){
		alert ("Kiwix Catalog is Older than 30 days.\n\nPlease click Refresh Kiwix Catalog in the menu.");
	}
}
function procZimCatalog() {
  // Uses installedZimCat, kiwixCatalog, langCodes, and langGroups
  // Calculates zimCatalog, zimGroups, langNames, zimsInstalled, zimsScheduled

  zimCatalog = {};
  zimGroups = {};
  zimLangs = [];

  // Add to zimCatalog

  procOneCatalog(installedZimCat['INSTALLED']);
  procOneCatalog(installedZimCat['WIP']);
  procOneCatalog(kiwixCatalog);

  // Create working arrays of installed and wip
  zimsInstalled = [];
  zimsScheduled = [];

  for (var id in installedZimCat['INSTALLED']){
    zimsInstalled.push(id);
    lang = installedZimCat['INSTALLED'][id]['language'];
    if (selectedLangs.indexOf(lang) == -1) // automatically select any language for which zim is installed
    selectedLangs.push (lang);
  }
  for (var id in installedZimCat['WIP']){
    zimsScheduled.push(id);
    lang = installedZimCat['WIP'][id]['language'];
    if (selectedLangs.indexOf(lang) == -1) // automatically select any language for which zim is being installed
    selectedLangs.push (lang);
  }

  if (selectedLangs.length == 0)
  selectedLangs.push (defaultLang); // default

  sortZimLangs(); // Create langNames from zimLangs and sort
  procZimLangs(); // Create language menu
  procZimGroups(); // Create zim list for selected languages

  return true;
}

function procOneCatalog(catalog){
	  if ($.isEmptyObject(catalog)){
      consoleLog("procOneCatalog found empty data");
      displayServerCommandStatus ("procOneCatalog found empty data")
      return;
    }
  else {
  //if (Object.keys(catalog).length > 0){
    for (var id in catalog) {
      var lang = catalog[id].language;
      if (lang in langGroups)
      lang = langGroups[lang]; // group synomyms like en/eng
      var cat = catalog[id].creator;

      if (!(lang in zimGroups)){
        var cats = {};
        cats[cat] = [];
        zimGroups[lang] = cats;
      }

      if (!(cat in zimGroups[lang]))
      zimGroups[lang][cat] = [];

      if (zimGroups[lang][cat].indexOf(id) == -1)
      zimGroups[lang][cat].push (id);

      zimCatalog[id] = catalog[id]; // add to working catalog
      if (zimLangs.indexOf(lang) == -1)
      zimLangs.push(lang);
    }
  }
}

function readableSize(kbytes) {
  if (kbytes == 0)
  return "0";
  var bytes = 1024 * kbytes;
  var s = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'];
  var e = Math.floor(Math.log(bytes) / Math.log(1024));
  return (bytes / Math.pow(1024, e)).toFixed(2) + " " + s[e];
}

function sortZimLangs(){
  langNames = [];
  for (var i in zimLangs){
    if (langCodes[zimLangs[i]] === undefined){ // for now ignore languages we don't know
      consoleLog('Language code ' + zimLangs[i] + ' not in langCodes.');
      continue;
    }
    var attr = {};
    attr.locname = langCodes[zimLangs[i]]['locname'];
    attr.code = zimLangs[i];
    attr.engname = langCodes[zimLangs[i]]['engname'];
    langNames.push(attr);
  }
  langNames = langNames.sort(function(a,b){
    if (a.locname < b.locname) return -1;
    else return 1;
    });
}

function getRachelStat(){
  var command = "GET-RACHEL-STAT";
  sendCmdSrvCmd(command, procRachelStat);
  return true;
}

function procRachelStat(data) {
  rachelStat = data;

  setRachelDiskSpace();
  var html = "";
  var htmlNo = "<b>NO</b>";
  var htmlYes = "<b>YES</b>";
  var installedHtml = htmlNo;
  var enabledHtml = htmlNo;
  var contentHtml = htmlNo;

  if (rachelStat["status"] == "INSTALLED")
    installedHtml = htmlYes;

  if (rachelStat["status"] == "ENABLED"){
    installedHtml = htmlYes;
    enabledHtml = htmlYes;
  }

  if (rachelStat["content_installed"] == true)
    contentHtml = htmlYes;

  $("#rachelInstalled").html(installedHtml);
  $("#rachelEnabled").html(enabledHtml);
  $("#rachelContentFound").html(contentHtml);

  var moduleList = [];

  if (rachelStat["content_installed"] == true){
    for (var title in rachelStat.enabled) {
      moduleList.push(title);
    }

    moduleList.sort();

    for (var idx in moduleList) {
    	html += '<tr><td>' + moduleList[idx] + '</td><td>';
    	if (rachelStat.enabled[moduleList[idx]].enabled == true)
    	  html += htmlYes + '</td></tr>'
    	else
    		html += htmlNo + '</td></tr>'
    }
    $("#rachelModules tbody").html(html);
    $("#rachelModules").show();
  }
  else
  	$("#rachelModules").hide();
}

function getDownloadList(){
	var zimCmd = 'LIST-LIBR {"sub_dir":"downloads/zims"}';
	var rachelCmd = 'LIST-LIBR {"sub_dir":"downloads/rachel"}';
	setDnldDiskSpace();
	$.when(sendCmdSrvCmd(zimCmd, procDnldZimList), sendCmdSrvCmd(rachelCmd, procDnldRachelList)).done(procDnldList);

  return true;
}

function procDnldZimList(data){
	downloadedFiles['zims'] = data;
}

function procDnldRachelList(data){
	downloadedFiles['rachel'] = data;
}

function procDnldList(){

  $("#downloadedFilesRachel").html(calcDnldListHtml(downloadedFiles.rachel.file_list));
  $("#downloadedFilesZims").html(calcDnldListHtml(downloadedFiles.zims.file_list));
  console.log("in procDnldList");
}

function calcDnldListHtml(list) {
	var html = "";
	list.forEach(function(entry) {
    console.log(entry);
    html += '<tr>';
    html += "<td>" + entry['filename'] + "</td>";
    html += "<td>" + entry['size'] + "</td>";
    html +=  '<td><input type="checkbox" name="' + entry['filename'] + '" id="' + entry['filename'] + '">' + "</td>";
    html +=  '</tr>';
  });
  return html;
}

function delDownloadedFiles() {
  $.when(
    delDownloadedFileList("downloadedFilesRachel", "rachel"),
    delDownloadedFileList("downloadedFilesZims", "zims"))
    .done(getDownloadList, refreshDiskSpace);
}

function delDownloadedFileList(id, sub_dir) {
  var delArgs = {}
	var fileList = [];
  $("#" + id + " input").each(function() {
    if (this.type == "checkbox") {
      if (this.checked)
      fileList.push(this.name);
    }
  });

  if (fileList.length == 0)
    return;

  delArgs['sub_dir'] = sub_dir;
  delArgs['file_list'] = fileList;

  var delCmd = 'DEL-DOWNLOADS ' + JSON.stringify(delArgs);
  return sendCmdSrvCmd(delCmd, genericCmdHandler);
}

// Util functions

function getJobStat()
{
  var command = "GET-JOB-STAT"
  sendCmdSrvCmd(command, procJobStat);
  return true;
}

function procJobStat(data)
{
  job_status = {};
  var html = "";
  var html_break = '<br>';

  data.forEach(function(entry) {
    //console.log(entry);
    html += "<tr>";
    var job_info = {};

    job_info['job_no'] = entry[0];
    html += "<td>" + entry[0] + "<BR>"; // job number
    // html +=  '<input type="checkbox" name="' gw_squid_whitelist + '" id="' xo-gw_squid_whitelist +'">';
    var jobId = "job_stat_id-" + entry[0];
    html +=  '<input type="checkbox" id="' + jobId + '">';
    html += "</td>";
    job_info['command'] = entry[1];
    html += '<td style="overflow: hidden; text-overflow: ellipsis">' + entry[1] + "</td>";

    result = entry[2].replace(/(?:\r\n|\r|\n)/g, html_break); // change newline to BR
    // result = result.replace(html_break+html_break, html_break); // remove blank lines, but doesn't work
    var idx = result.indexOf(html_break);
    if (idx =0) result = result.substring(html_break.length); // strip off first newline
    idx = result.lastIndexOf(html_break);
    if (idx >=0) result = result.substring(0,idx); // strip off last newline
    job_info['result'] = result;

    idx = result.lastIndexOf(html_break);  // find 2nd to last newline
    var result_end = "";
    if (idx >=0) result_end = result.substring(0,idx + html_break.length);
    html += '<td> <div class = "statusJobResult">' + result + "</div></td>";

    job_info['status'] = entry[3];
    html += "<td>" + entry[3] + "</td>";
    job_info['status_date'] = entry[4];
    html += "<td>" + entry[4] + "</td>";

    html += "</tr>";

    // there should be one or two parts
    var cmd_parse = entry[5].split(" ");
    job_info['cmd_verb'] = cmd_parse[0];
    if(cmd_parse.length == 0 || typeof cmd_parse[1] === 'undefined')
      job_info['cmd_args'] = ""
    else
      job_info['cmd_args'] = JSON.parse(cmd_parse[1]);

    consoleLog(job_info);
    job_status[job_info['job_no']] = job_info;

  });
  $( "#jobStatTable tbody" ).html(html);
  $( "#jobStatTable div.statusJobResult" ).each(function( index ) {
    $(this).scrollTop(this.scrollHeight);
  });
  today = new Date();
  $( "#statusJobsRefreshTime" ).html("Last Refreshed: <b>" + today.toLocaleString() + "</b>");
}

function cancelJob(job_id)
{
  var command = "CANCEL-JOB"
  var cmd_args = {}
  cmd_args['job_id'] = job_id;
  cmd = command + " " + JSON.stringify(cmd_args);
  $.when(sendCmdSrvCmd(cmd, genericCmdHandler)).then(getJobStat);
  return true;
}

function cancelJobFunc(job_id)
{
  var command = "CANCEL-JOB"
  var cmd_args = {}
  cmd_args['job_id'] = job_id;
  cmd = command + " " + JSON.stringify(cmd_args);
  return $.Deferred( function () {
  	var self = this;
  	sendCmdSrvCmd(cmd, genericCmdHandler);
  	});
}

function getSysMem()
{
  var command = "GET-MEM-INFO"
  sendCmdSrvCmd(command, procSysMem);
  return true;
}

function procSysMem(data)
{
  //alert ("in procSysMem");
  consoleLog(data);
  var sysMemory = data['system_memory'];
  var html = "";
  for (var i in sysMemory)
  html += sysMemory[i] + "<BR>"

  $( "#sysMemory" ).html(html);
  //consoleLog(jqXHR);
  return true;
}

function refreshDiskSpace(){

  //$.when(sendCmdSrvCmd("GET-STORAGE-INFO", procSysStorageDat),sendCmdSrvCmd("GET-ZIM-STAT", procZimStatInit)).then(procDiskSpace);
  $.when(getSpaceAvail(), getZimStat()).then(displaySpaceAvail);
}

function procDiskSpace(){
  //procZimGroups(); - don't call because resets check boxes
  sumCheckedZimDiskSpace();
  displaySpaceAvail();
}

function getSysStorage()
{
  var command = "GET-STORAGE-INFO"
  sendCmdSrvCmd(command, procSysStorageLite);
  return true;
}

function procSysStorageLite(data)
{
  //alert ("in procSysStorage");

  consoleLog(data);
  var sysStorageRpt = data['system_fs'];
  var html = "";
  for (var i in sysStorageRpt)
    html += sysStorageRpt[i] + "<BR>"

  $( "#sysStorage" ).html(html);
  //consoleLog(jqXHR);
  return true;
}

// need to rewrite the function below for lvm, etc.
function procSysStorage()
{
  //alert ("in procSysStorage");

  consoleLog(data);
  sysStorage.raw = data;

  var html = "";
  for (var i in sysStorage.raw) {
    var dev = sysStorage.raw[i];
    html += "<b>" + dev.device + "</b>";
    html += " " + dev.desc;
    html += " " + dev.type;
    html += " " + dev.size;
    html += ":<BR><BR>";

    for (var j in sysStorage.raw[i].blocks){
      var block = dev.blocks[j];
      html += block.part_dev;
      if (block.part_dev == 'unallocated')
      html += " " + block.size;
      else {
        html += " " + block.type;
        html += " " + block.size;
        if (block.part_prop.TYPE != "\"swap\""){
          html += " (" + block.part_prop.avail_in_megs + "M avail)";
          html += " " + block.part_prop.mount_point;
          if (block.part_prop.mount_point == "/"){
            sysStorage.root.part_dev = block.part_dev;
            sysStorage.root.avail_in_megs = block.part_prop.avail_in_megs;
          }
          if (block.part_prop.mount_point == "/library"){
            sysStorage.library.part_dev = block.part_dev;
            sysStorage.library.avail_in_megs = block.part_prop.avail_in_megs;
            sysStorage.library.partition = true;
          }
        }
      }
      html += "<BR>";
    }
    html += "<BR>";
  }
  $( "#sysStorage" ).html(html);

  //consoleLog(jqXHR);
  return true;
}

function getSpaceAvail (){
  return sendCmdSrvCmd("GET-SPACE-AVAIL", procSpaceAvail);
}

function procSpaceAvail (data){
  sysStorage.library_on_root = data.library_on_root; // separate library partition (T/F)
	sysStorage.root = data.root;
	if (! sysStorage.library_on_root)
    sysStorage.library = data.library;
}

function displaySpaceAvail(){
	// display space available on various panels
	// assumes all data has been retrieved and is in data structures
  setZimDiskSpace();
  setRachelDiskSpace();
  setDnldDiskSpace();
}

function setZimDiskSpace(){
  var html = calcLibraryDiskSpace();

  html += "Estimated Space Required: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";

  // make space estimate double the size due to needing both the download and the deployed files
  html += "<b>" + readableSize(sysStorage.zims_selected_size * 2) + "</b>"
  $( "#zimDiskSpace" ).html(html);
}

function setRachelDiskSpace(){
  var html = calcLibraryDiskSpace();

  html += "Estimated Space Required: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";

  html += "<b>" + "23G (X 2 for Download)" + "</b>"
  $( "#rachelDiskSpace" ).html(html);
}

function setDnldDiskSpace() {
	var html = calcLibraryDiskSpace();
	$( "#dnldDiskSpace" ).html(html);
}

function calcLibraryDiskSpace(){
  var html = "Library Space Available : <b>";

  //var zims_selected_size;

  // library space is accurate whether separate partition or not

	if (sysStorage.library_on_root)
	  html += readableSize(sysStorage.root.avail_in_megs * 1024) + "</b><BR>";
	else
    html += readableSize(sysStorage.library.avail_in_megs * 1024) + "</b><BR>";

  return html;
}

function updateZimDiskSpace(cb){
  var zim_id = cb.name
  updateZimDiskSpaceUtil(zim_id, cb.checked);
}

function updateZimDiskSpaceUtil(zim_id, checked){
  var zim = zimCatalog[zim_id]
  var size =  parseInt(zim.size);

  var zimIdx = selectedZims.indexOf(zim_id);

  if (checked){
    if (zimsInstalled.indexOf(zim_id) == -1){ // only update if not already installed zims
      sysStorage.zims_selected_size += size;
      selectedZims.push(zim_id);
    }
  }
  else {
    if (zimIdx != -1){
      sysStorage.zims_selected_size -= size;
      selectedZims.splice(zimIdx, 1);
    }
  }

  setZimDiskSpace();

}

function sumCheckedZimDiskSpace(){
  var zim_id = '';
  var zim = {};
  var size = 0;

  sysStorage.zims_selected_size = 0;

  for (var i in selectedZims){
    zim_id = selectedZims[i]
    zim = zimCatalog[zim_id];
    var size =  parseInt(zim.size);

    sysStorage.zims_selected_size += size;
  }
}

function getInetSpeed(){
  var command = "GET-INET-SPEED";
  sendCmdSrvCmd(command, procInetSpeed, "GET-INET-SPEED");
  $( "#intSpeed1" ).html("Working ...");
  //$('#myModal').modal('show');
  return true;
}

function procInetSpeed(data){
  //alert ("in procInetSpeed");
  consoleLog(data);
  var intSpeed = data["internet_speed"];
  var html = "";
  for (var i in intSpeed)
  html += intSpeed[i] + "<BR>"

  $( "#intSpeed1" ).html(html);
  return true;
}

function getInetSpeed2(){
  var command = "GET-INET-SPEED2"
  sendCmdSrvCmd(command, procInetSpeed2, "GET-INET-SPEED2");
  $( "#intSpeed2" ).html("Working ...");
  return true;
}

function procInetSpeed2(data){
  //alert ("in procInetSpeed2");
  consoleLog(data);
  var intSpeed = data["internet_speed"];
  var html = "";
  for (var i in intSpeed)
  html += intSpeed[i] + "<BR>"

  $( "#intSpeed2" ).html(html);
  //consoleLog(jqXHR);
}


function rebootServer()
{
  var command = "REBOOT"
  sendCmdSrvCmd(command, genericCmdHandler);
  alert ("Reboot Initiated");
  return true;
}

function poweroffServer()
{
  var command = "POWEROFF"
  sendCmdSrvCmd(command, genericCmdHandler);
  alert ("Shutdown Initiated");
  return true;
}

function getHelp(arg)
{
  $.get( "help/" + arg, function( data ) {
    var rst = data;
    var convert = new Markdown.getSanitizingConverter().makeHtml;
    var html = convert(rst);
    $( "#helpItem" ).html( html );
  });
  return true;
}

function showAboutSummary()
{
  //consoleLog("in showAboutSummary");
  var html = '<table>';

  html += '<tr><td ><b>Version:</b></td>';
  html += '<td>' + xsce_ini.runtime.runtime_branch + '</td></tr>';
  html += '<td><b>Date Installed:</b></td>';
  html += '<td>' + xsce_ini.runtime.runtime_date + '</td></tr>';
  html += '<td><b>Commit ID:</b></td>';
  html += '<td>' + xsce_ini.runtime.runtime_commit + '</td></tr>';

  html += "</tr></table>";

  $( "#aboutSummaryText" ).html( html );
}

function getServerInfo() {
	displayServerCommandStatus("Checking Server Connection");
  var resp = $.ajax({
    type: 'GET',
    cache: false,
    global: false, // don't trigger global error handler
    url: 'server-info.php',
    dataType: 'json'
  })
  .done(function( data ) {
    serverInfo.xsce_server_ip = data.xsce_server_ip;
    serverInfo.xsce_client_ip = data.xsce_client_ip;
    serverInfo.xsce_cmdsrv_running = data.xsce_cmdsrv_running;

    consoleLog(serverInfo);
    if (serverInfo.xsce_cmdsrv_running == "FALSE"){
      displayServerCommandStatus("XSCE-CMDSRV is not running");
      alert ("XSCE-CMDSRV is not running on the server");
    }
    else
      displayServerCommandStatus("Successfully connected to Server");
  })
  .fail(getServerInfoError);

  return resp;
}

function getServerInfoError (jqXHR, textStatus, errorThrown){
  jsonErrhandler (jqXHR, textStatus, errorThrown); //check for json errors
  serverInfo.xsce_server_found = "FALSE";
  consoleLog("Connection to Server failed.");
  displayServerCommandStatus('Connection to Server <span style="color:red">FAILED</span>.');
  alert ("Connection to Server failed.\n Please make sure your network settings are correct,\n that the server is turned on,\n and that the web server is running.");
}


function formCommand(cmd_verb, args_name, args_obj)
{
  var cmd_args = {}
  cmd_args[args_name] = args_obj;
  var command = cmd_verb + " " + JSON.stringify(cmd_args);
  consoleLog(command);

  return command;
}

// monitor for awhile and use version if no problems present

function sendCmdSrvCmd(command, callback, buttonId, errCallback, cmdArgs) {
  // takes following arguments:
  //   command - Command to send to cmdsrv
  //   callback - Function to call on success
  //   buttonId - Optional ID of button to disable and re-enable
  //   errCallback - Optional function to call if return from cmdsrv has error object; not the same as an error in ajax
  //   cmdArgs - Optional arguments to original command for use by errCallback
  //   TODO  - add assignmentVar so can assign variable before running callback
  //alert ("in sendCmdSrvCmd(");
  //consoleLog ('buttonid = ' + buttonId);;

  // skip command if init has already failed - not sure this works
  if (initStat.active == true && initStat.error == true){
  	var deferredObject = $.Deferred();
  	logServerCommands (command, "failed", "Init already failed");
  	return deferredObject.reject();
  }

  //consoleLog ("command: " + command);

  var cmdVerb = command.split(" ")[0];
  logServerCommands (cmdVerb, "sent");

  if (buttonId === undefined)
  buttonId = "";
  else
    make_button_disabled('#' + buttonId, true);

    var resp = $.ajax({
      type: 'POST',
      url: xsceCmdService,
      data: {
        command: command
      },
      dataType: 'json',
      buttonId: buttonId
    })
    //.done(callback)
    .done(function(dataResp, textStatus, jqXHR) {
    	//var dataResp = data;
    	if ("Error" in dataResp){
    	  cmdSrvError(cmdVerb, dataResp);
    	  if (typeof errCallback != 'undefined'){
    	    consoleLog(errCallback);
    	    errCallback(data, cmdArgs);
    	  }
    	}
    	else {
    		var data = dataResp.Data;
    	  callback(data);
    	  logServerCommands (cmdVerb, "succeeded", "", dataResp.Resp_time);
    	}
    })
    .fail(jsonErrhandler)
    .always(function() {
      make_button_disabled('#' + this.buttonId, false);
    });

    return resp;
}

// Report errors that came from cmdsrv or cmd-service

function cmdSrvError (cmdVerb, dataResp){
	var errorText = dataResp["Error"];
	consoleLog(errorText);
  logServerCommands (cmdVerb, "failed", errorText);
  cmdSrvErrorAlert (cmdVerb, dataResp)
  initStat["error"] = true;
}

function cmdSrvErrorAlert (cmdVerb, dataResp){
	var errorText = dataResp["Error"];
	var alertText = cmdVerb + " FAILED and reported " + errorText;

	if (initStat["active"] == false)
	  alert(alertText);
	else {
		// during init only alert if flagged from server
		if (("Alert" in dataResp) && ! (errorText in initStat["alerted"])){
		  alert(alertText);
		  initStat["alerted"][errorText] = true;
		}
  }
}

// Generic ajax error handler called by all .fail events unless global: false set

function ajaxErrhandler (event, jqxhr, settings, thrownError) {
	consoleLog("in .ajaxError");
  consoleLog(event);
  consoleLog(jqxhr);
  consoleLog(settings);
  consoleLog(thrownError);

  // For commands sent to command server
  if (settings.url == xsceCmdService){
    var cmdstr = settings.data.split("command=")[1];
    var cmdVerb = cmdstr.split(/[ +]/)[0];
    consoleLog(cmdVerb);
    logServerCommands (cmdVerb, "failed", jqxhr.statusText);
    // see if we are connected to server
    consoleLog(jqxhr.statusText, serverInfo.xsce_server_found);
    //if (jqxhr.statusText == "error" && serverInfo.xsce_server_found == "TRUE"){
    if (jqxhr.statusText == "error"){
      consoleLog("calling getServerInfo");
      getServerInfo();
    }
  }
  if (initStat["active"] == true)
    initStat["error"] = true;
}

// Error handler mostly for json errors, which should be bugs or bad data

function jsonErrhandler (jqXHR, textStatus, errorThrown)
{
  // only handle json parse errors here, others in ajaxErrHandler
  if (textStatus == "parserror") {
    //alert ("Json Errhandler: " + textStatus + ", " + errorThrown);
    displayServerCommandStatus("Json Errhandler: " + textStatus + ", " + errorThrown);
  }
  //consoleLog("In Error Handler logging jqXHR");
  consoleLog(textStatus);
  consoleLog(errorThrown);
  consoleLog(jqXHR);

  return false;
}

function consoleLog (msg)
{
  console.log(msg); // for IE there can be no console messages unless in tools mode
}

function logServerCommands (command, status, extraData="", respTime=0)
{
  var msg = "";

  switch (status) {
    case "sent":
        msg = "Command " + command + " sent to server";
        break;
    case "succeeded":
        msg = command + ' <span style="color:green">SUCCEEDED</span> (' + Math.round(1000 * respTime) + ' ms)';
        break;
    case "failed":
        msg = command + ' <span style="color:red">FAILED</span>';
        if (extraData != "" && extraData != "error"){
          msg += ' and returned ' + extraData;
        }

        break;

  }
  displayServerCommandStatus(msg);
}

function displayServerCommandStatus (msg)
{
  var initSelector = "#initLog";
  var logSelector = "#serverCmdLog";
  var now = new Date();

  $(logSelector).prepend(now.toLocaleString() + ": " + msg + "<BR>");
  if (initStat.active == true)
    $(initSelector).prepend(now.toLocaleString() + ": " + msg + "<BR>");
}

function init ()
{
  //$('#initDataModal').modal('show');

  initStat["active"] = true;
  initStat["error"] = false;
  initStat["alerted"] = {};

  displayServerCommandStatus("Starting init");

  getServerInfo(); // see if we can connect

  $.when(
    sendCmdSrvCmd("GET-ANS-TAGS", getAnsibleTags),
    sendCmdSrvCmd("GET-WHLIST", getWhitelist),
    $.when(sendCmdSrvCmd("GET-VARS", getInstallVars), sendCmdSrvCmd("GET-ANS", getAnsibleFacts),sendCmdSrvCmd("GET-CONF", getConfigVars),sendCmdSrvCmd("GET-XSCE-INI", procXsceIni)).done(initConfigVars),
    $.when(getLangCodes(),readKiwixCatalog(),sendCmdSrvCmd("GET-ZIM-STAT", procZimStatInit)).done(procZimCatalog),
    getSpaceAvail(),
    waitDeferred(3000))
    .done(initDone)
    .fail(function () {
    	displayServerCommandStatus('<span style="color:red">Init Failed</span>');
    	consoleLog("Init failed");
    	})
}

function initDone ()
{
	if (initStat["error"] == false){
	  consoleLog("Init Finished Successfully");
	  displayServerCommandStatus('<span style="color:green">Init Finished Successfully</span>');
	  displaySpaceAvail(); // display on various panels
	  // now turn on navigation
	  navButtonsEvents();
	  //$('#initDataModal').modal('hide');
  } else {
    consoleLog("Init Failed");
    displayServerCommandStatus('<span style="color:red">Init Failed</span>');
    //$('#initDataModalResult').html("<b>There was an error on the Server.</b>");
  }
  initStat["active"] = false;
}

function waitDeferred(msec) {
    var deferredObject = $.Deferred();

    setTimeout(function() { deferredObject.resolve();  }, msec);

    return deferredObject.promise();
}
