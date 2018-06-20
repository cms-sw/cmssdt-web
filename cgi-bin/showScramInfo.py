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
        self.errPkg   = {}
        self.warnPkg  = {}
        return
    
    # --------------------------------------------------------------------------------

    def analyzeLogFile(self, lines):

        scramErrRe = {
                       'error' : [ re.compile('\*+.?ERROR:.*?\s*src/([A-Za-z].*?/[A-Za-z].*?)/.*'),
                                   re.compile('.*?/MakeData/DirCache.mk:\d+:\s+No such file exists:\s+src/([A-Za-z].*?/[A-Za-z].*?)/.*'),
                                 ],
                       'warning' : [ re.compile('\*+WARNING:.*?\s*src/([A-Za-z].*?/[A-Za-z].*?)/.*'),
                                   ],
                       'errorEx' : [ re.compile('^\s*\*+\s*ERROR:.*'),
                                   ],
                       'warningEx' : [ re.compile('^\s*\*+\s*WARNING:.*'),
                                     ],
                     }
        self.errPkg  = {}
        self.warnPkg = {}
	self.errEx = 0
	self.warnEx = 0
        startFound = False
        for line in lines:
            if not startFound:
                if "Resetting caches" in line: startFound = True
                continue
            elif ">> Building CMSSW version" in line: break
            
            found = False
            for stype in scramErrRe:
                if found: break
                for item in scramErrRe[stype]:
                    res = item.match(line)
                    if not res: continue
                    found = True
                    if stype == 'warningEx': self.warnEx += 1
                    elif stype == 'errorEx': self.errEx  += 1
                    else:
                        pkg = res.group(1)
                        if stype == 'error':
			    if pkg not in self.errPkg : self.errPkg[pkg]=[]
                            self.errPkg[pkg].append(line)
                        elif stype == 'warning':
                            if pkg not in self.warnPkg : self.warnPkg[pkg]=[]
                            self.warnPkg[pkg].append(line)
                    break
        return

    def showResults(self):

        pkgList = self.errPkg.keys()
        nErr = len(pkgList)
        if len(pkgList) > 0:
            self.formatter.writeH3('A total of '+str(nErr)+' SCRAM errors in '+str(len(pkgList))+' packages found in build.')
            self.formatter.startTable([50,5],['package', 'scram errors'])
            pkgList.sort()
            for pkg in pkgList:
                err = len(self.errPkg[pkg])
                self.formatter.writeRow([pkg, str(err)])
            self.formatter.endTable()
        else:
            self.formatter.writeH3('No SCRAM errors found in build.')

        pkgList = self.warnPkg.keys()
        nWarn = len(pkgList)
        if len(pkgList) > 0:
            self.formatter.writeH3('A total of '+str(nWarn)+' SCRAM warnings in '+str(len(pkgList))+' packages found in build.')
            self.formatter.startTable([50,5],['package', 'scram warnings'])
            pkgList.sort()
            for pkg in pkgList:
                warn = len(self.warnPkg[pkg])
                self.formatter.writeRow([pkg, str(warn)])
            self.formatter.endTable()
        else:
            self.formatter.writeH3('No SCRAM warnings found in build.')

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
        self.formatter.writeH2("CMSSW Integration Build Scram Info")

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
        self.showResults()
        
        return


def main():

    
    style = """
    <link rel="stylesheet" type="text/css" href="http://cern.ch/cms-sdt/intbld.css">\n
    """

    fmtr = Formatter.SimpleHTMLFormatter(title="CMSSW Integration Build Scram Info", style=style)

    sana = ScramAnalyzer(fmtr)
    sana.showLog()

if __name__ == '__main__' :
    main()
    
