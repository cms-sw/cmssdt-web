#!/usr/bin/env python

# make sure this is first to trap also problems in includes later
import cgitb; cgitb.enable() ## cgitb.enable(display=0, logdir=os.getcwd()+"/../cgi-logs/")

import os, sys, cgi, time, re

scriptPath = '/afs/cern.ch/cms/sdt/web/cgi-bin/'
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

import Formatter

import config

def cleanPath(path):
    return os.path.normpath(os.path.join('/',path))

# ================================================================================


class LogViewer(object):

    def __init__(self, formatter):

        self.formatter = formatter
        
        self.buildList = {}
        self.platCycleMap = {}
        
        self.platList = ['slc4_ia32_gcc345', 'slc4_amd64_gcc345', 'slc4_ia32_gcc412']
        
        self.webLogDirBase = '/data/sdt/buildlogs/'
        self.webLogDir = None # to be set up as base+plat+'/www/'
        
        self.webLogURLBase = config.siteInfo['HtmlPath']+'/rc/'
        self.webLogCGIBase = config.siteInfo['CgiHtmlPath']
        self.days = [ 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun' ]

        self.commands = None

        self.cycList = ['3.1', '3.0', '2.2']

        return

    # --------------------------------------------------------------------------------

    def getCommands(self, path):

        fileName = 'logs/addOnTests.pkl'
        dbPath = os.path.join(path, fileName)
        # print "reading commands from ", dbPath
        
        if not os.path.exists( dbPath ):
            print "ERROR: pkl file "+dbPath+"does not exist"
            return

        import pickle
        self.commands = pickle.load( open(dbPath,'r') )

        # print self.commands

        # self.showCommands()
        
        return

    # --------------------------------------------------------------------------------
    
    def showCommands(self):

        print "found ", len(self.commands), ' commands:'

        n1 = 0
        n2 = 0
        n3 = 0
        maxLen = 50
        for dirName, cmdList in self.commands.items():
            n1+=1
            print "%-10s  [1]: %s ..." % (dirName, cmdList[0])
            if len(cmdList) > 1:
                n2+=1
                print "       [2]: %s ..." % (  "".join(cmdList[1]))
                if len(cmdList) > 2:
                    n3+=1
                    print "        [3]: %s ..." % ( ' '.join( cmdList[3]) )

        print n1, 'commands with  one  step,'
        print n2, 'commands with  two  steps'
        print n3, 'commands with three steps'

        return
    
    # --------------------------------------------------------------------------------

    def getSummaryLogInfo(self, path):
        passed  = []
        failed  = []
        notrun  = []

        stepOK   = 0
        stepFail = 0
        
        logFileName = path+'/../addOnTests.log'
            
        try:
            sumLog = open(logFileName, 'r')
            lines = sumLog.readlines()
            sumLog.close()
        except:
            # print "ERROR openig or reading logFile", logFileName
            # formatter.writeH3( "ERROR opening or reading logFile: "+logFileName )
            return passed, failed, timeout, notrun, stepOK, stepFail
        
        logRe = re.compile('(cmsRun|cmsDriver.py)\s+(.*?)\s:\s([PF].*?D)\s.*')

        for line in lines:

            logMatch = logRe.match(line)
            if logMatch:
                runOrDriver = logMatch.group(1)
                cmd = logMatch.group(2).replace(' ','_')
                res = logMatch.group(3)

                if 'PASSED' in res:
                    stepOK += 1
                    passed.append(runOrDriver+'_'+cmd)
                elif 'FAILED' in res:
                    stepFail += 1
                    failed.append(runOrDriver+'_'+cmd)

        return passed, failed, notrun, stepOK, stepFail
    
    # --------------------------------------------------------------------------------

    def getLogFile(self, addOnDir):

        self.logFiles = []
        logArch1 = addOnDir+"/addOnTests.zip"
        logArch = addOnDir+"/addOnTests.tgz"
        from commands import getstatusoutput
        if os.path.exists(logArch1):
            err, out = getstatusoutput("unzip -l "+logArch1+" | grep '.log$' | sed s'|.* ||'")
            for log in out.split("\n"):
                self.logFiles.append(log)
        elif os.path.exists(logArch):
            err, out = getstatusoutput('tar tzf '+logArch)
            for log in out.split("\n"):
                self.logFiles.append(log)
        else:
            from glob import glob
            for log in glob(addOnDir+"/addOnTests/logs/*.log"):
                self.logFiles.append(os.path.basename(log))
        return
    
    def findLogFile(self, lfPar):
        for log in self.logFiles:
            if log.startswith(lfPar[:100]):
                return "addOnTests/logs/"+log
        return ''
    
    # --------------------------------------------------------------------------------

    def showLogs(self):

        pathReq = ""
        try:
            scriptName = os.environ["SCRIPT_NAME"]
            requestURI = os.environ["REQUEST_URI"]
            pathReq = cleanPath( requestURI.replace(scriptName,'') )
        except:
            scriptName = sys.argv[0]
            pathReq = sys.argv[1]
            pass

        newStyle = True
	if pathReq.endswith("&new"):
	    newStyle = True
	    pathReq = pathReq[:-4]
	elif pathReq.endswith("&old"):
	    newStyle = False
	    pathReq = pathReq[:-4]

        self.formatter.writeAnchor(ref='top')
        self.formatter.writeH2("CMSSW Integration Build Add-On Test log viewer")

        topLogDir = '/data/sdt/buildlogs/'
        fullPath = topLogDir + pathReq
        normPath = os.path.normpath( fullPath )

        logBaseURL = config.siteInfo['HtmlPath']+'/rc/'

        self.formatter.write("Logs available in " + normPath+'/logs/')

        ib = normPath.split('/')[-2]
        self.formatter.writeH3('Integration Build ' + ib)

        self.getCommands(normPath)

        passed, failed, notrun, stepOK, stepFail = self.getSummaryLogInfo(normPath)
        rvCmds = self.commands

        if stepOK==0 and stepFail==0 :
            self.formatter.writeH3("Test logs not yet available")
            return

	stepRes = [[0,0,0,0],[0,0,0,0]]
	actualSteps = 0

        xRest = {}
        for dirName, cmdList in self.commands.items():
	    step = -1
            for i in range(0,len(stepRes[0])):
                try:
                    cmd = cmdList[i]
                except:
                    continue
                cmdx = cmd.replace(' ','_')
                if 'ln -s ' in cmd :
                    continue
                if cmdx in notrun:
                    continue
                step += 1
		res = 'passed'
                if cmdx in failed:
                   stepRes[1][step]=stepRes[1][step]+1
		   res = 'failed'
                else:
                    stepRes[0][step]=stepRes[0][step]+1
		xRest[dirName+':'+str(i)] = res
                if actualSteps<step: actualSteps = step

        self.formatter.startTable ( [15, 15, 15, 15, 15], ['Step','total', 'passed', 'failed'])
	for i in range(0,actualSteps+1):
          self.formatter.writeRow(['step'+str(i+1)  , str(stepRes[0][i]+stepRes[1][i]), str(stepRes[0][i]), str(stepRes[1][i])])
        self.formatter.endTable()

        self.formatter.writeH3('<a href="'+logBaseURL+pathReq+'/../addOnTests.log"> Summary log (addOnTests.log) </a>')

        self.formatter.showLine()

        msgFail = '<a> Failed tests : ('+str(stepFail)+') '
        msgFail += '</a> <br />'
        self.formatter.writeH3(msgFail + ' <a href="#top"> back to top </a> ')

        self.formatter.writeH3('<a name="tests"> Add-On tests: ('+str(stepOK)+' tests) </a> <br /> <a href="#top"> back to top </a> ')

        rows = {}
        styles = {}
        orderedKeys = []

        logFilePath = logBaseURL+pathReq+'/logs/'
        self.getLogFile(os.path.dirname(normPath))
        topCgiLogString = config.siteInfo['CgiHtmlPath']+'buildlogs/'+pathReq.split('/')[1]+'/'+ib+'/'
        for dirName, cmdList in self.commands.items():
            step = 0
            for i in range(0,len(stepRes[0])):
	        styleClass = 'passed'
		try:
		    styleClass = xRest[dirName+':'+str(i)]
		except:
		    continue
                cmd = cmdList[i]
                lfPart = cmd.replace("'",'').replace('/','_').replace(' ',"_")
                logFileName = 'cmsDriver-'+dirName+'_'+'%s.log' % lfPart
                logFileName = self.findLogFile(logFileName)

                outLine = '<a href="'+topCgiLogString+logFileName+'">'
                if newStyle:
                    outLine += 'log</a>&nbsp;&nbsp;<a class="detail" name="'+dirName+'cmd" onclick="showHide(this) ">cmd</a> <a class="info" name="'+dirName+'cmd" onclick="showHide(this) ">hide<br/>'
                else:
                    outLine += dirName+'</a>'

                outLine += '<br/><font size="-1" color="black">'+cmd.replace("../",'')+'</font>'
                if newStyle:
                     outLine += '</a>'

                if dirName not in rows.keys():
                    rows[dirName] = {}
                    styles[dirName] = {}
                rows[dirName][step] = outLine 
                styles[dirName][step] = styleClass 
                if dirName not in orderedKeys: orderedKeys.append(dirName)

                step += 1

        if newStyle:
            self.formatter.startTable( [10, 30, 20, 20, 20], ['id', 'test', 'step1', 'step2', 'step3'])
            self.formatter.write('<b><a href="'+scriptName+pathReq+'&old">Old Style</a></b>')
        else:
            self.formatter.startTable( [10, 30, 30, 30], ['id', 'step1', 'step2', 'step3'])
            self.formatter.write('<b><a href="'+scriptName+pathReq+'&new">New Style</a></b>')
        
        num = 0
        orderedKeys.sort() 
        for sample in orderedKeys:
            num += 1
            row = [ str(num) ]
            rowStyles = ['']
	    if newStyle:
	        style = "passed"
		rdata = sample
		for x in styles[sample]:
		    if styles[sample][x] == "failed":
		        style = "failed"
			break
		row.append( sample )
		rowStyles.append('"'+style+' '+'left"')   
            for step in range(0,3):
                try:
                    row.append( rows[sample][step] )
                    rowStyles.append( styles[sample][step] )
                except KeyError:
                    row.append( '&nbsp;' )
                    rowStyles.append( '' )
                    
            self.formatter.writeStyledRow(row, rowStyles)
        self.formatter.endTable()

        return 

# ================================================================================

def main():

    style = """
    <link rel="stylesheet" type="text/css" href="/SDT/html/intbld.css">\n
    
    <style type="text/css">  
    .info { display: none; }
    .mainTable { table-layout:fixed; }
    .showOld { font-size: 18; text-decoration: underline; padding: 20px}
    td.left {
      text-align: left;
    }
    </style>  

    <script type="text/javascript" src="/SDT/html/jsExt/jquery.js"></script>
    <script>
    function showHide(obj){
        var myname = obj.name;
        $(".detail[name='"+myname+"']").toggle();
        $(".info[name='"+myname+"']").toggle();
    }
    </script>
    """

    fmtr = Formatter.SimpleHTMLFormatter(title="Add-On Test Logs from CMSSW Integration Build", style=style)

    lv = LogViewer(fmtr)
    lv.showLogs()

    return


main()
