#!/usr/bin/env python
# encoding: utf-8
"""
showValgrindFile.py

Created by Andreas Pfeiffer on 2009-04-01.
Copyright (c) 2009 CERN. All rights reserved.
"""
import cgi
import cgitb; cgitb.enable()

import sys
import os, stat, glob, re

import config

from Formatter import SimpleHTMLFormatter
from helpers   import getStamp

def cleanPath(path):
	return os.path.normpath(os.path.join('/',path.replace('?','')))

def main():
    
    js = '''
<link rel="stylesheet" type="text/css" href="@HOST@/valgrind.css">

<!-- 
<style type="text/css">  
@import url(css.css);  
</style>  
-->

<style type="text/css">  
.info { display: none; }
</style>  


<script type="text/javascript" src="@HOST@/jsExt/jquery.js"></script>

<script type="text/javascript">
function showHide(obj){
    myname = obj.name;
    $(".detail[name='"+myname+"']").toggle();
    $(".info[name='"+myname+"']").toggle();
}
</script>

<script type="text/javascript">
$(document).ready(function()
{
// make the "summary" and "hide summary" underlined
$(".detail").css('text-decoration', "underline");
$(".info").css('text-decoration', "underline");
// color rows of tables alternatively for even/odd rows
$("tr:even").css("background-color", 'rgb(234, 235, 255)');
$("tr:odd").css("background-color",  'rgb(211, 214, 255)');
// //for table stackFrame, select different colors for even/odd rows
$("table.stackFrame tr:even").css("background-color", 'rgb(234, 235, 255)'); // "#ccffcc");
$("table.stackFrame tr:odd").css("background-color",  'rgb(211, 214, 255)'); // "#99ffff");
});
</script>
    
<script type="text/javascript">
if (window.XMLHttpRequest)
  {
  xhttp=new XMLHttpRequest();
  }
else // Internet Explorer 5/6
  {
  xhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
var xmlFileName="%s";
xhttp.open("GET",xmlFileName,false);
xhttp.send("");
xmlDoc=xhttp.responseXML; 

document.write("<h2>Valgrind report for "+xmlFileName.split('/').pop()+"<\/h2>");
document.write("<h3>IB: %s<\/h3>");

String.prototype.entityify = function () {
return this.replace(/&/g, "&amp;").replace(/[<]/g, "&lt;").replace(/[>]/g, "&gt;");
}

var x=xmlDoc.getElementsByTagName("error");
var docHasAux = 0;
if (x.length > 0) {
    document.write("<h3>Found "+x.length+" errors in total.<\/h3>")
    document.write("<table border='1' cellpadding='3'>");
    document.write("<tr>");
    document.write("<td><b> #        <\/b><\/td>");
    document.write("<td><b> type      <\/b><\/td>");
    document.write("<td><b> detail #, lib, function <\/b><\/td>");
    document.write("<\/tr>");
    for (i=0;i<x.length;i++) { // loop all errors in doc
        document.write("<tr><td>");
        document.write(i);
        document.write("<\/td><td>");
        document.write(x[i].getElementsByTagName("what")[0].childNodes[0].nodeValue);
        document.write("<br/> &nbsp; <br/>");
	if (x[i].getElementsByTagName("auxwhat").length > 0) {
	   for (ia=0; ia<x[i].getElementsByTagName("auxwhat").length; ia++) {
	      document.write(x[i].getElementsByTagName("auxwhat")[ia].childNodes[0].nodeValue);
	      document.write("<br /> &nbsp; <br />");
	   }
	   docHasAux = x[i].getElementsByTagName("auxwhat").length;
	}
        document.write("<\/td><td>");
        document.write("<table class='stackFrame' border='0'>");
        var sf = x[i].getElementsByTagName("stack")[0].getElementsByTagName("frame");
        var details = "";

        for (f=0;f<sf.length;f++) {
            libName  = sf[f].getElementsByTagName("obj")[0].childNodes[0].nodeValue.split('/').pop();
            fnNameRaw = sf[f].getElementsByTagName("fn")[0].childNodes[0].nodeValue;
	    var fnName = String(fnNameRaw).entityify();
            if ( sf[f].getElementsByTagName("dir").length > 0 ) {
                pathName = sf[f].getElementsByTagName("dir")[0].childNodes[0].nodeValue;
                fileName = sf[f].getElementsByTagName("file")[0].childNodes[0].nodeValue;
                lineName = sf[f].getElementsByTagName("line")[0].childNodes[0].nodeValue;
		while (lineName.length < 3) {
		   lineName = '0'+lineName;
		}
                dirNames = pathName.split('/');
                dirName = "";
                for (id=dirNames.length-3; id<dirNames.length; id++) { dirName += dirNames[id]+'/'; } 
                fnName += '<br /> <i>from: <a href="http://cmslxr.fnal.gov/lxr/source/'+dirName+fileName+'?v=%s'+'#'+lineName+'">'+dirName+fileName+" : "+lineName+'<\/a><\/i>';

            }
            if (f == 0) { // write out the first row always, the other ones only on click
                row = "<tr><td>"+f+"<\/td><td>"+libName+"<\/td><td>"+fnName+"<\/td><\/tr>";
                document.write(row);
            } else {
                row = "<tr><td>"+f+"<\/td><td>"+libName+"<\/td><td>"+fnName+"<\/td><\/tr>";
                document.write(row);
            }
        }

	if (docHasAux > 0) {
	  if (x[i].getElementsByTagName("stack").length > 0) {
	   var auxs = x[i].getElementsByTagName("auxwhat");
	   for (ia=0; ia<docHasAux; ia++) {
	     var emptyRow = "<tr><td colspan=3><hr /><\/td><\/tr>";
	     emptyRow += "<tr><td>&nbsp;<\/td><td> <b>Auxiliary information:<\/b> <\/td><td><b>";
	     emptyRow +=auxs[ia].childNodes[0].nodeValue;
	     emptyRow +="<\/b><\/td><\/tr>";
	     document.write(emptyRow);
  	     var sf = x[i].getElementsByTagName("stack")[ia+1].getElementsByTagName("frame");

	     for (f=0;f<sf.length;f++) {
	       libName  = sf[f].getElementsByTagName("obj")[0].childNodes[0].nodeValue.split('/').pop();
	       fnNameRaw= sf[f].getElementsByTagName("fn")[0].childNodes[0].nodeValue;
	       var fnName = String(fnNameRaw).entityify();
	       if ( sf[f].getElementsByTagName("dir").length > 0 ) {
                   pathName = sf[f].getElementsByTagName("dir")[0].childNodes[0].nodeValue;
		   fileName = sf[f].getElementsByTagName("file")[0].childNodes[0].nodeValue;
		   lineName = sf[f].getElementsByTagName("line")[0].childNodes[0].nodeValue;
		   while (lineName.length < 3) {
		      lineName = '0'+lineName;
		   }
		   dirNames = pathName.split('/');
		   dirName = "";
		   for (id=dirNames.length-3; id<dirNames.length; id++) { dirName += dirNames[id]+'/'; } 
		   fnName += '<br /> <i>from: <a href="http://cmslxr.fnal.gov/lxr/source/'+dirName+fileName+'?v=%s'+'#'+lineName+'">'+dirName+fileName+" : "+lineName+'<\/a><\/i>';
		   
	       }
	       row = "<tr><td>"+f+"<\/td><td>"+libName+"<\/td><td>"+fnName+"<\/td><\/tr>";
	       document.write(row);
            } // end for sf.length

	    }// end for ia<docHasAux
          } 
	}
        document.write("<\/table>");
        document.write("<\/td><\/tr>");
    }
    document.write("<\/table>");
}
document.write("<p><\/p>");
</script>
'''
    js = js.replace('@HOST@',config.siteInfo['HtmlPath'])

    form = cgi.FieldStorage()

    ## cgi.print_form(form)
    txtOnly  = form.has_key('txt')

    fmtr = SimpleHTMLFormatter(title='Valgrind report')

    # set some defaults
    scriptName = sys.argv[0]
    requestURI = '/'.join(sys.argv)
    try:
    	scriptName = os.environ["SCRIPT_NAME"]
    	requestURI = os.environ["REQUEST_URI"]
    except:
    	pass
    pathReq = cleanPath( requestURI.replace(scriptName,'') )

    # reporter.info([pathReq])
    topPath = config.siteInfo['qaPath']
    topURL  = config.siteInfo['OutHtml']
    fullPath = topURL + os.path.normpath(pathReq)
    normPath = fullPath 
    # fmtr.write( normPath,'<br/>' )

    ib = normPath.split('/')[8]
    day, stamp, cycle = getStamp(ib)

    script = js % (normPath, ib, day.capitalize(), day.capitalize())
    fmtr.addScriptCode(script)

    fmtr.write("") # dummy write to output script code ...

if __name__ == '__main__':
	main()

