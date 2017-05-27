/* Copyright (c) 2007 Lev Muchnik <LevMuchnik@gmail.com>. All rights reserved.
 * You may copy and modify this script as long as the above copyright notice,
 * this condition and the following disclaimer is left intact.
 * This software is provided by the author "AS IS" and no warranties are
 * implied, including fitness for a particular purpose. In no event shall
 * the author be liable for any damages arising in any way out of the use
 * of this software, even if advised of the possibility of such damage.
 * $Date: 2007-10-03 19:08:15 -0700 (Wed, 03 Oct 2007) $
 */

function LoadXML(ParentElementID,URL) 
{
		var xmlHolderElement = GetParentElement(ParentElementID);
		if (xmlHolderElement==null) { return false; }
		ToggleElementVisibility(xmlHolderElement);
		return RequestURL(URL,URLReceiveCallback,ParentElementID);
}
function LoadXMLDom(ParentElementID,xmlDoc) 
{
	if (xmlDoc) {
		var xmlHolderElement = GetParentElement(ParentElementID);
		if (xmlHolderElement==null) { return false; }
		while (xmlHolderElement.childNodes.length) { xmlHolderElement.removeChild(xmlHolderElement.childNodes.item(xmlHolderElement.childNodes.length-1));	}
		var Result = ShowXML(xmlHolderElement,xmlDoc.documentElement,0);
		
		var ReferenceElement = document.createElement('div');
		var Link = document.createElement('a');		
		Link.setAttribute('href','http://www.levmuchnik.net/Content/ProgrammingTips/WEB/XMLDisplay/DisplayXMLFileWithJavascript.html');
		var TextNode = document.createTextNode('Source: Lev Muchnik');
		Link.appendChild(TextNode);

		xmlHolderElement.appendChild(Link);
		return Result;
	}
	else { return false; }
}
function LoadXMLString(ParentElementID,XMLString) 
{
	xmlDoc = CreateXMLDOM(XMLString);
	return LoadXMLDom(ParentElementID,xmlDoc) ;
}
////////////////////////////////////////////////////////////
// HELPER FUNCTIONS - SHOULD NOT BE DIRECTLY CALLED BY USERS
////////////////////////////////////////////////////////////
function GetParentElement(ParentElementID)
{
	if (typeof(ParentElementID)=='string') {	return document.getElementById(ParentElementID);	}
	else if (typeof(ParentElementID)=='object') { return ParentElementID;} 
	else { return null; }
}
function URLReceiveCallback(httpRequest,xmlHolderElement)
{
	  try {
            if (httpRequest.readyState == 4) {
                if (httpRequest.status == 200) {
					var xmlDoc = httpRequest.responseXML;
					if (xmlHolderElement && xmlHolderElement!=null) {
							xmlHolderElement.innerHTML = '';
							return LoadXMLDom(xmlHolderElement,xmlDoc);
					}
                } else {
                    return false;
                }
            }
        }
        catch( e ) {
            return false;
        }	
}
function RequestURL(url,callback,ExtraData) { // based on: http://developer.mozilla.org/en/docs/AJAX:Getting_Started
        var httpRequest;
        if (window.XMLHttpRequest) { // Mozilla, Safari, ...
            httpRequest = new XMLHttpRequest();
            if (httpRequest.overrideMimeType) { httpRequest.overrideMimeType('text/xml'); }
        } 
        else if (window.ActiveXObject) { // IE
            try { httpRequest = new ActiveXObject("Msxml2.XMLHTTP");   } 
            catch (e) {
				   try { httpRequest = new ActiveXObject("Microsoft.XMLHTTP"); } 
				   catch (e) {}
            }
        }
        if (!httpRequest) { return false;   }
        httpRequest.onreadystatechange = function() { callback(httpRequest,ExtraData); };
        httpRequest.open('GET', url, true);
        httpRequest.send('');
		return true;
    }
function CreateXMLDOM(XMLStr) 
{
	if (window.ActiveXObject)
	 {
		  xmlDoc=new ActiveXObject("Microsoft.XMLDOM"); 
		  xmlDoc.loadXML(XMLStr);	
		  return xmlDoc;
	}
	else if (document.implementation && document.implementation.createDocument)	  {
		  var parser=new DOMParser();
		  return parser.parseFromString(XMLStr,"text/xml");
	}
	else {
		return null;
	}
}		

var IDCounter = 1;
var NestingIndent = 15;
function ShowXML(xmlHolderElement,RootNode,indent)
{
	if (RootNode==null || xmlHolderElement==null) { return false; }
	var Result  = true;
	var TagEmptyElement = document.createElement('div');
	TagEmptyElement.className = 'Element';
	TagEmptyElement.style.position = 'relative';
	TagEmptyElement.style.left = NestingIndent+'px';
	if (RootNode.childNodes.length==0) { 
    var ClickableElement = AddTextNode(TagEmptyElement,'','Clickable') ;
    ClickableElement.id = 'div_empty_' + IDCounter;	  
    AddTextNode(TagEmptyElement,'<','Utility') ;
    AddTextNode(TagEmptyElement,RootNode.nodeName ,'NodeName') 
    for (var i = 0; RootNode.attributes && i < RootNode.attributes.length; ++i) {
      CurrentAttribute  = RootNode.attributes.item(i);
      AddTextNode(TagEmptyElement,' ' + CurrentAttribute.nodeName ,'AttributeName') ;
      AddTextNode(TagEmptyElement,'=','Utility') ;
      AddTextNode(TagEmptyElement,'"' + CurrentAttribute.nodeValue + '"','AttributeValue') ;
    }
    AddTextNode(TagEmptyElement,' />') ;
    xmlHolderElement.appendChild(TagEmptyElement);	
    //SetVisibility(TagEmptyElement,true);    
	}
	else { // mo child nodes
    
    var ClickableElement = AddTextNode(TagEmptyElement,'+','Clickable') ;
    ClickableElement.onclick  = function() {ToggleElementVisibility(this); }
    ClickableElement.id = 'div_empty_' + IDCounter;	
		
    AddTextNode(TagEmptyElement,'<','Utility') ;
    AddTextNode(TagEmptyElement,RootNode.nodeName ,'NodeName') 
    for (var i = 0; RootNode.attributes && i < RootNode.attributes.length; ++i) {
      CurrentAttribute  = RootNode.attributes.item(i);
      AddTextNode(TagEmptyElement,' ' + CurrentAttribute.nodeName ,'AttributeName') ;
      AddTextNode(TagEmptyElement,'=','Utility') ;
      AddTextNode(TagEmptyElement,'"' + CurrentAttribute.nodeValue + '"','AttributeValue') ;
    }

    AddTextNode(TagEmptyElement,'>  </','Utility') ;
    AddTextNode(TagEmptyElement,RootNode.nodeName,'NodeName') ;
    AddTextNode(TagEmptyElement,'>','Utility') ;
    xmlHolderElement.appendChild(TagEmptyElement);	
    SetVisibility(TagEmptyElement,false);
    //----------------------------------------------
    
    var TagElement = document.createElement('div');
    TagElement.className = 'Element';
    TagElement.style.position = 'relative';
    TagElement.style.left = NestingIndent+'px';
    ClickableElement = AddTextNode(TagElement,'-','Clickable') ;
    ClickableElement.onclick  = function() {ToggleElementVisibility(this); }
    ClickableElement.id = 'div_content_' + IDCounter;		
    ++IDCounter;
    AddTextNode(TagElement,'<','Utility') ;
    AddTextNode(TagElement,RootNode.nodeName ,'NodeName') ;
    
    for (var i = 0; RootNode.attributes && i < RootNode.attributes.length; ++i) {
        CurrentAttribute  = RootNode.attributes.item(i);
        AddTextNode(TagElement,' ' + CurrentAttribute.nodeName ,'AttributeName') ;
        AddTextNode(TagElement,'=','Utility') ;
        AddTextNode(TagElement,'"' + CurrentAttribute.nodeValue + '"','AttributeValue') ;
    }
    AddTextNode(TagElement,'>','Utility') ;
    TagElement.appendChild(document.createElement('br'));
    var NodeContent = null;
    for (var i = 0; RootNode.childNodes && i < RootNode.childNodes.length; ++i) {
      if (RootNode.childNodes.item(i).nodeName != '#text') {
        Result &= ShowXML(TagElement,RootNode.childNodes.item(i),indent+1);
      }
      else {
        NodeContent =RootNode.childNodes.item(i).nodeValue;
      }					
    }			
    if (RootNode.nodeValue) {
      NodeContent = RootNode.nodeValue;
    }
    if (NodeContent) {	
      var ContentElement = document.createElement('div');
      ContentElement.style.position = 'relative';
      ContentElement.style.left = NestingIndent+'px';			
      AddTextNode(ContentElement,NodeContent ,'NodeValue') ;
      TagElement.appendChild(ContentElement);
    }			
    AddTextNode(TagElement,'  </','Utility') ;
    AddTextNode(TagElement,RootNode.nodeName,'NodeName') ;
    AddTextNode(TagElement,'>','Utility') ;
    xmlHolderElement.appendChild(TagElement);	
  }
	
	// if (indent==0) { ToggleElementVisibility(TagElement.childNodes(0)); } - uncomment to collapse the external element
	return Result;
}
function AddTextNode(ParentNode,Text,Class) 
{
	NewNode = document.createElement('span');
	if (Class) {  NewNode.className  = Class;}
	if (Text) { NewNode.appendChild(document.createTextNode(Text)); }
	if (ParentNode) { ParentNode.appendChild(NewNode); }
	return NewNode;		
}
function CompatibleGetElementByID(id)
{
	if (!id) { return null; }
	if (document.getElementById) { // DOM3 = IE5, NS6
		return document.getElementById(id);
	}
	else {
		if (document.layers) { // Netscape 4
			return document.id;
		}
		else { // IE 4
			return document.all.id;
		}
	}
}
function SetVisibility(HTMLElement,Visible)
{
	if (!HTMLElement) { return; }
	var VisibilityStr  = (Visible) ? 'block' : 'none';
	if (document.getElementById) { // DOM3 = IE5, NS6
		HTMLElement.style.display =VisibilityStr; 
	}
	else {
		if (document.layers) { // Netscape 4
			HTMLElement.display = VisibilityStr; 
		}
		else { // IE 4
			HTMLElement.id.style.display = VisibilityStr; 
		}
	}
}
function ToggleElementVisibility(Element)
{
	if (!Element|| !Element.id) { return; }
	try {
		ElementType = Element.id.slice(0,Element.id.lastIndexOf('_')+1);
		ElementID = parseInt(Element.id.slice(Element.id.lastIndexOf('_')+1));
	}
	catch(e) { return ; }
	var ElementToHide = null;
	var ElementToShow= null;
	if (ElementType=='div_content_') {
		ElementToHide = 'div_content_' + ElementID;
		ElementToShow = 'div_empty_' + ElementID;
	}
	else if (ElementType=='div_empty_') {
		ElementToShow= 'div_content_' + ElementID;
		ElementToHide  = 'div_empty_' + ElementID;
	}
	ElementToHide = CompatibleGetElementByID(ElementToHide);
	ElementToShow = CompatibleGetElementByID(ElementToShow);
	if (ElementToHide) { ElementToHide = ElementToHide.parentNode;}
	if (ElementToShow) { ElementToShow = ElementToShow.parentNode;}
	SetVisibility(ElementToHide,false);
	SetVisibility(ElementToShow,true);
}
