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

import config

class ScramAnalyzer(object):

    def __init__(self, fmtr):
        self.formatter = fmtr
        self.dupInfo = {}

    
    # --------------------------------------------------------------------------------

    def analyzeLogFile(self, lines, fileName):

        emptyLine = False
        issueItem = ""
        where = []
        for line in lines:

            if "Searching for " in line : continue
            if "**** SKIPPING " in line : continue

            if line.strip() == "":
                emptyLine = True
            
            if emptyLine:
                self.dupInfo[issueItem] = where
                issueItem = ""
                where = []
                emptyLine = False
            else:
                if line[0] == ' ':
                    where.append( line.strip() )
                else:
                    issueItem = line.strip()
                emptyLine = False

        return
    # --------------------------------------------------------------------------------

    def showLogFile(self, fileName):

        issueList = self.dupInfo.keys()
        
        if len(issueList) > 0:
            self.formatter.writeH3('')
            delimiter = '<br />'
            if fileName == 'dupDict-lostDefs.log':
                self.formatter.startTable([50,5],['classes_def.xml', 'wrongly defines the following objects '])
                delimiter = '<br /><hr/>'
            else:
                self.formatter.startTable([50,5],['object found multiple times', 'libs/xml files the object is found in'])
            issueList.sort()
            for pkg in issueList:
                errIn = self.dupInfo[pkg]
                err = [ cgi.escape(x) for x in errIn ] # escape each element to show "<"
                self.formatter.writeRow([cgi.escape(pkg.decode('ascii','ignore')), delimiter.join(err)])
            self.formatter.endTable()
        else:
            self.formatter.writeH3('No duplicate dictionaries found for '+fileName+' were found ! Great ! :) ')

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

        summary = False
        if '/summaryOnly' in pathReq : 
            pathReq = pathReq.replace('/summaryOnly', '')
            summary = True
            
        self.formatter.writeAnchor(ref='top')
        self.formatter.writeH2("CMSSW Integration Build Dictionary Duplication Info")

        topLogDir = '/data/sdt/buildlogs/'
        fullPath = topLogDir + pathReq
        normPath = os.path.normpath( fullPath )

        try:
            logFile = open(normPath, 'r')
            lines = logFile.readlines()
            logFile.close()
        except Exception, e:
            self.formatter.write("no log file found. Please try again later.")
            self.formatter.write(str(e))
            return
        
        self.analyzeLogFile(lines, os.path.basename(normPath))
        if summary:
            self.formatter.write('found '+str(len(self.dupInfo.keys()))+' packages with issues.')
            return
        
        # now the output for the detail-page:
        logBaseURL = config.siteInfo['HtmlPath']+'rc'

        logLink ='<a href="'+logBaseURL+pathReq+'"> '+normPath+'</a>'
        self.formatter.write("Log file available at " + logLink)

        ib = normPath.split('/')[-3]
        self.formatter.writeH3('Integration Build ' + ib)

        self.formatter.writeH3('Information about duplicated dictionaries or dictionaries defined in the wrong place (lib). ')

        self.showLogFile(os.path.basename(normPath))
        
        return


def main():

    
    style = """
    <link rel="stylesheet" type="text/css" href="http://cern.ch/cms-sdt/intbld.css">\n
    """

    fmtr = Formatter.SimpleHTMLFormatter(title="CMSSW Integration Build Dictionary Duplication Info", style=style)

    sana = ScramAnalyzer(fmtr)
    sana.showLog()

if __name__ == '__main__' :
    main()
    
