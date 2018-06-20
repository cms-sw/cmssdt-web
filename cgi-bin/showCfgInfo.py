#!/usr/bin/env python

# make sure this is first to trap also problems in includes later
import cgitb; cgitb.enable() ## cgitb.enable(display=0, logdir=os.getcwd()+"/../cgi-logs/")

import os, sys, cgi, time, re

scriptPath = '/afs/cern.ch/cms/sdt/web/cgi-bin/'
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

import Formatter

def cleanPath(path):
    return os.path.normpath(os.path.join('/',path))



class ScramAnalyzer(object):

    def __init__(self, fmtr):
        self.formatter = fmtr
        
    
    # --------------------------------------------------------------------------------

    def analyzeLogFile(self, lines):

        cfgInfo = {}
        for line in lines:
            try:
                pkg, num = line.split(':')
                if num.strip() == '0': continue
                cfgInfo[pkg] = num
            except:
                raise
            
        pkgList = cfgInfo.keys()
        if len(pkgList) > 0:
            self.formatter.writeH3('Found a total of '+str(len(pkgList))+' packages with old style config files')
            self.formatter.startTable([50,5],['package', '# cf[fig] files'])
            pkgList.sort()
            for pkg in pkgList:
                err = cfgInfo[pkg]
                self.formatter.writeRow([pkg, str(err)])
            self.formatter.endTable()
        else:
            self.formatter.writeH3('No packages with old style config files found')

        return 

    # --------------------------------------------------------------------------------

    def showLog(self):

        pathReq = ""
        try:
            scriptName = os.environ["SCRIPT_NAME"]
            requestURI = os.environ["REQUEST_URI"]
            pathReq = cleanPath( requestURI.replace(scriptName,'') )
        except:
            pathReq = sys.argv[1]
            pass

        toolTipInclude = '<script type="text/javascript" src="http://cern.ch/cms-sdt/wz_tooltip.js"></script>\n'
        self.formatter.write(toolTipInclude)

        self.formatter.writeAnchor(ref='top')
        self.formatter.writeH2("CMSSW Integration Build CFG Info")

        topLogDir = '/data/sdt/buildlogs/'
        fullPath = topLogDir + pathReq
        normPath = os.path.normpath( fullPath )

        logBaseURL = 'http://cmssdt.cern.ch/SDT/html/rc/'

        logLink ='<a href="'+logBaseURL+pathReq+'"> '+normPath+'</a>'
        self.formatter.write("Log file available at " + logLink)

        ib = normPath.split('/')[-2]
        self.formatter.writeH3('Integration Build ' + ib)

        try:
            logFile = open(normPath, 'r')
            lines = logFile.readlines()
            logFile.close()
        except:
            self.formatter.write("no log")
            return
        
        self.analyzeLogFile(lines)

        return


def main():

    
    style = """
    <link rel="stylesheet" type="text/css" href="http://cern.ch/cms-sdt/intbld.css">\n
    """

    fmtr = Formatter.SimpleHTMLFormatter(title="CMSSW Integration Build CFG Info", style=style)

    sana = ScramAnalyzer(fmtr)
    sana.showLog()

if __name__ == '__main__' :
    main()
    
