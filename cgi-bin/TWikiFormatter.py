#!/usr/bin/env python2

import os, sys, string

from xml.parsers import expat

# ================================================================================

class TWikiFormatter :

    def __init__(self, title="CMS SDT pages ", style=None, outFile=sys.stdout, release=None) :
        import time

        self.headersDone = False
        self.title=title
        self.style = style
        self.outFile = outFile
        self.format = ""
	self.raw = 0

        self.ib = release

        return

    def __del__(self) :
        if self.headersDone :
            self.trailers()
        else: # in case nothing has been written yet, output an empty page ...
            self.outFile.write( "Content-Type: text/html" + '\n')     # HTML is following
            self.outFile.write( '\n')   # blank line, end of headers
            self.outFile.write( "<html> " + '\n')
            self.outFile.write( "</html> " + '\n')
        
        return

    def showLine(self) :
        self.headers()
        self.outFile.write( "<hr />" + '\n')
        return
    
    def write(self, arg="", bold=False) :
        self.headers()
        if bold:
            self.writeB(arg)
        else:
            self.outFile.write( arg + '\n')
        return

    def writeBr(self) :
        self.headers()
        self.outFile.write( "<br /> <br /> " + '\n')
        return
    
    def writeB(self, arg="") :
        self.headers()
        self.outFile.write( "<b> " + arg + " </b>" + '\n')
        return
    
    def writeH1(self, arg="") :
        self.headers()
        self.outFile.write( "<h1> " + arg + " </h1>" + '\n')
        return
    
    def writeH2(self, arg="") :
        self.headers()
        self.outFile.write( "<h2> " + arg + " </h2>" + '\n')
        return

    def writeH3(self, arg="", styleClass=None) :
        self.headers()
        if styleClass:
            self.outFile.write( '<h3 class="h'+styleClass+'">' + arg + " </h3>" + '\n')
        else:
            self.outFile.write( "<h3> " + arg + " </h3>" + '\n')
        return

    def startUl(self) :
	self.headers()
	self.outFile.write( "<ul>"+'\n')
    def writeLi(self, args) :
	self.outFile.write( "<li>"+args+"</li>"+'\n')
    def endUl(self) :
	self.outFile.write("</ul>"+'\n')
    
    def writeAnchor(self, ref="") :
        self.headers()
        self.outFile.write( '<br /> <a name="' + ref + '"></a> <a href="#top">back to top</a><br />')
        return
    
    def startTable(self, colSizes, colLabels, id=None, cls=None) :
        # we assume that headers are done by now !!
        tableString = '<table border="1"  '
        if id:
            tableString += ' id="'+id+'" '
        if cls:
            tableString += ' class="'+cls+'" '
        tableString += '>'
        self.outFile.write( tableString + '\n')

        self.outFile.write( " <thead>\n  <tr>"  + '\n')
        for col in colLabels :
            self.outFile.write( "   <th> <b>" + col + "</b> </th>" + '\n')
        self.outFile.write( "  </tr>\n</thead>" + '\n')
        self.outFile.write( "  <tbody>" + '\n')
        return

    def writeRow(self, args, bold=False) :
        # we assume that headers are done by now !!
        self.outFile.write( " <tr>" + '\n')
        for arg in args:
            if string.strip(str(arg)) == "" : arg = "&nbsp;"
            if bold: self.outFile.write( '<td class=cellbold> ' )
            else:    self.outFile.write( "  <td> " )
            self.outFile.write( arg )
            
            self.outFile.write( " </td>" + '\n')
        self.outFile.write( " </tr> " + '\n')

        return

    def writeStyledRow(self, args, styles) :
        # we assume that headers are done by now !!
        self.outFile.write( " <tr>" + '\n')
        for arg, cellStyle in zip(args, styles):
            if string.strip(str(arg)) == "" : arg = "&nbsp;"
            cellStyle = cellStyle.strip()
            if cellStyle != '' : self.outFile.write( '<td class='+cellStyle+'> ' )
            else:    self.outFile.write( "  <td> " )
            self.outFile.write( arg )
            self.outFile.write( " </td>" + '\n')
        self.outFile.write( " </tr> " + '\n')

        return

    def endTable(self) :
        # we assume that headers are done by now !!
        self.outFile.write( "</tbody>" + '\n')
        self.outFile.write( "</table>" + '\n')
                
    # --------------------------------------------------------------------------------
    def headers(self) :
	import config
        # make sure to write the headers only once ...
        if not self.headersDone :
	    self.outFile.write( "Content-Type: text/html" + '\n')     # HTML is following
	    self.outFile.write("""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<meta http-equiv="X-UA-Compatible" content="IE=EmulateIE7" />
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
"""
)
            if self.style:
                self.outFile.write( self.style + '\n')
            
            self.outFile.write( "<TITLE>" + self.title + "</TITLE>" + '\n')
	    self.outFile.write( """
<script type="text/javascript">
function enlarge(el) {
	el.width *= 2;
	el.height*= 2;
}
function ensmall(el) {
	el.width = 300;
	el.height = 200;
}
</script>
<style type="text/css">
#info {background:#f8f8f8; border:0;}

/* ================================================================ 
This copyright notice must be untouched at all times.

The original version of this stylesheet and the associated (x)html
is available at http://www.cssplay.co.uk/menus/final_drop.html
Copyright (c) 2005-2008 Stu Nicholls. All rights reserved.
This stylesheet and the associated (x)html may be modified in any 
way to fit your requirements.
=================================================================== */

.menu {width:745px; height:32px; position:relative; border-right:1px solid #000; font-family:arial, sans-serif;}
/* hack to correct IE5.5 faulty box model */
* html .menu {width:746px; w\idth:745px;}
/* remove all the bullets, borders and padding from the default list styling */
.menu ul {padding:0;margin:0;list-style-type:none;}
.menu ul ul {width:149px; z-index:100}
/* float the list to make it horizontal and a relative positon so that you can control the dropdown menu positon */
.menu li {float:left;width:149px;position:relative}
/* style the links for the top level */
.menu a, .menu a:visited {display:block;font-size:12px;text-decoration:none; color:#fff; width:138px; height:30px; border:1px solid #000; border-width:1px 0 1px 1px; background:#09c; padding-left:10px; line-height:29px; font-weight:bold;}
/* a hack so that IE5.5 faulty box model is corrected */
* html .menu a, * html .menu a:visited {width:149px; w\idth:138px;}

/* style the second level background */
.menu ul ul a.drop, .menu ul ul a.drop:visited {background:#d4d8bd no-repeat 130px center }
/* style the second level hover */
.menu ul ul a.drop:hover{background:#c9ba65 no-repeat 130px center}
.menu ul ul :hover > a.drop {background:#c9ba65 no-repeat 130px center;}
/* style the third level background */
.menu ul ul ul a, .menu ul ul ul a:visited {background:#e2dfa8;}
/* style the third level hover */
.menu ul ul ul a:hover {background:#b2ab9b;}


/* hide the sub levels and give them a positon absolute so that they take up no room */
.menu ul ul {visibility:hidden;position:absolute;height:0;top:31px;left:0; width:149px;border-top:1px solid #000;}
/* another hack for IE5.5 */
* html .menu ul ul {top:30px;t\op:31px;}

/* position the third level flyout menu */
.menu ul ul ul{left:149px; top:-1px; width:149px;}

/* position the third level flyout menu for a left flyout */
.menu ul ul ul.left {left:-149px;}

/* style the table so that it takes no ppart in the layout - required for IE to work */
.menu table {position:absolute; top:0; left:0; border-collapse:collapse;;}

/* style the second level links */
.menu ul ul a, .menu ul ul a:visited {background:#d4d8bd; color:#000; height:auto; line-height:1em; padding:5px 10px; width:128px;border-width:0 1px 1px 1px;}
/* yet another hack for IE5.5 */
* html .menu ul ul a, * html .menu ul ul a:visited {width:150px;w\idth:128px;}

/* style the top level hover */
.menu a:hover, .menu ul ul a:hover{color:#000; background:#b7d186;}
.menu :hover > a, .menu ul ul :hover > a {color:#000; background:#b7d186;}

/* make the second level visible when hover on first level list OR link */
.menu ul li:hover ul,
.menu ul a:hover ul{visibility:visible; }
/* keep the third level hidden when you hover on first level list OR link */
.menu ul :hover ul ul{visibility:hidden;}
/* make the third level visible when you hover over second level list OR link */
.menu ul :hover ul :hover ul{ visibility:visible;}

</style>

	<style type="text/css" title="currentStyle">
		@import "%s/jsExt/dataTables/media/css/demo_page.css";
		@import "%s/jsExt/dataTables/media/css/demo_table.css";
	</style>

    <script type="text/javascript" src="%s/jsExt/jquery.js"></script>

    <script type="text/javascript" src="%s/js/igpSummary.js"></script>

    <script>
    function showHide(obj){
        myname = obj.name;
        $(".detail[name='"+myname+"']").toggle();  // .toggle('slow');
        $(".info[name='"+myname+"']").toggle();
    }
    </script>

    <script>
    $(document).ready(function()
    {
    // make the "summary" and "hide summary" underlined
    $(".detail").css('text-decoration', "underline");
    $(".info").css('text-decoration', "underline");
    });
    // var id=$("#id").attr("value");

    </script>


""" % (config.siteInfo['HtmlPath'], config.siteInfo['HtmlPath'], config.siteInfo['HtmlPath'], config.siteInfo['HtmlPath']) )
    
	    self.outFile.write('	<link rel="stylesheet" type="text/css" href="'+config.siteInfo['HtmlPath']+'colors.css">\n')
            self.outFile.write('	<link rel="stylesheet" type="text/css" href="'+config.siteInfo['HtmlPath']+'intbld.css">\n')
	    self.outFile.write("""
<TITLE> CMSSW Integration Build Scram Info</TITLE>
</head>
<body>

""")
        self.headersDone = True

        return

    # --------------------------------------------------------------------------------
    def trailers(self) :
        # write only if headers have been written ...
        if self.headersDone :
            self.outFile.write( "</body>" + '\n')
            self.outFile.write( "</html> " + '\n')
            pass
        return

    
