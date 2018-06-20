#!/usr/bin/env python

# make sure this is first to trap also problems in includes later
import cgitb; cgitb.enable() ## cgitb.enable(display=0, logdir=os.getcwd()+"/../cgi-logs/")

import os, sys, cgi, time, re

scriptPath = '/afs/cern.ch/cms/sdt/web/cgi-bin/'
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

import Formatter
import config
import getRVCmds
from glob import glob

def cleanPath(path):
    return os.path.normpath(os.path.join('/',path))

# ================================================================================


class LogViewer(object):

    def __init__(self, formatter):
        self.formatter = formatter
        return

    # --------------------------------------------------------------------------------

    def readLogMessageInfo(self, path):
        self.LogMessages = {}
        import pickle
	for fileName in glob(path+"/runTheMatrixMsgs.pkl*"):
          self.LogMessages.update(pickle.load( open(fileName,'r') ))
        return
    
    # --------------------------------------------------------------------------------

    def getSummaryLogInfo(self, path, steps):
        passed = {}; failed = {}; timeout = {}; notrun = {}; stepOK = {}; stepFail = {}
        for i in range(1,steps+1):
          step = 'step'+str(i)
          passed[step]  = []
          failed[step]  = []
          timeout[step] = []
          notrun[step]  = []
          stepOK[step]  = 0
          stepFail[step]= 0
          
        logRe = re.compile('\s*(\w.*?)\s*((Step\d+-[PNF].*?\s+)+)\s*-\s*.*\s*exit:\s*(([-]*\d+\s*)+).*$')
        for logFileName in glob(path+'/runall.log*'):
          try:
            sumLog = open(logFileName, 'r')
            lines = sumLog.readlines()
            sumLog.close()
          except:
            return passed, failed, timeout, notrun, stepOK, stepFail
        
          for line in lines:
            if not ' exit: ' in line: continue
            logMatch = logRe.match(line)
            if logMatch:
                jobId = logMatch.group(1).replace(' ','_')
                stepsData  = logMatch.group(2).split()
                exitCodes  = logMatch.group(4).split()
                xsteps = len(exitCodes)
		if xsteps != len(stepsData): continue
		for i in range(xsteps):
                  try:    exitCode = int(exitCodes[i])
                  except: exitCode = -9
                  step  = 'step'+str(i+1)
                  res   = stepsData[i]
                  if 'NOTRUN' in res:
                    notrun[step].append(jobId)
                  elif 'PASSED' in res:
                    stepOK[step] += 1
                    passed[step].append(jobId)
                  elif 'FAILED' in res:
                    stepFail[step] += 1
                    if exitCode == 36608 or exitCode == 35072 : timeout[step].append(jobId)
                    else:  failed[step].append(jobId)
        return passed, failed, timeout, notrun, stepOK, stepFail
    
    # --------------------------------------------------------------------------------

    def getBuildComparisonLogInfo(self, path):
        passed  = []
        failed  = []
        timeout = []
        notrun  = []
        report_path = {}
        report_status = {}
        stepOK   = 0
        stepFail = 0
        lines = []
        logRe = re.compile('\s*(\w.*?)\s*Comparison-([PNF].*?)\s*report:\s*([a-zA-Z0-9/_//./-]*)')
	for logFileName in glob(path+"/runall-comparison.log*"):
          try:
              sumLog = open(logFileName, 'r')
              lines += sumLog.readlines()
              sumLog.close()
          except:
              pass
          for line in lines:
            logMatch = logRe.match(line)
            if logMatch:
                job = logMatch.group(1)
                sample = job.replace(' ','_')
                comparisonRes = logMatch.group(2)
                try:
                    report_path[sample] = (str(logMatch.group(3).strip().replace(' ','_'))).strip()
                except:
                    report_path[sample] = ('')

                if 'NOTRUN' in comparisonRes  :
                    notrun.append(job.replace(' ','_'))
                    report_status[sample] = 'notrun'
                elif 'PASSED' in comparisonRes:
                    stepOK += 1
                    passed.append(job.replace(' ','_'))
                    report_status[sample] = 'passed'
                elif 'FAILED' in comparisonRes:
                    stepFail += 1
                    failed.append(job.replace(' ','_'))
                    report_status[sample] = 'failed'

        return passed, failed, timeout, notrun, stepOK, stepFail, report_path, report_status
    
    def getLogFiles(self, path):

        logFileMap = {}
        Logs = []
        logArch = path+"/../../pyRelValMatrixLogs.tgz"
        logArch1 = path+"/../../pyRelValMatrixLogs.zip"
        from commands import getstatusoutput
        if os.path.exists(logArch1):
            err, out = getstatusoutput("unzip -l "+logArch1+" | grep '.log$' | sed s'|.* ||'")
            for lf in out.split("\n"):
                 Logs.append(lf)
        elif os.path.exists(logArch):
            err, out = getstatusoutput("tar tzf "+logArch+" | grep '.log$'")
            for lf in out.split("\n"):
                 Logs.append(lf)
        else:
          for lfn in glob(path+'/*/*.log'):
              lf    = lfn.replace(path+'/','')
              Logs.append(lf)

        for lf in Logs:
            path  = lf.split('/')[0]
            fName = lf.split('/')[-1].replace('.log','')
            step  = fName.split("_")[0]
            logFileMap[step+'_'+path] = lf
        return logFileMap
    
    # --------------------------------------------------------------------------------
    def showLogs(self):

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
        self.formatter.writeH2("CMSSW Integration Build test log viewer")

        topLogDir = '/data/sdt/buildlogs/'
        fullPath = topLogDir + pathReq
        normPath = os.path.normpath( fullPath )

        logBaseURL = 'http://cmssdt.cern.ch/SDT/html/rc/'
        DQMReportsBaseURL = 'http://cmssdt.cern.ch/SDT/html/dqm/'

        self.formatter.write("Logs available in " + normPath)

        ib = normPath.split('/')[-3]
        backToPortal = ' -- <a href="'+config.siteInfo['CgiHtmlPath']+'showIB.py">Back to IB portal</a>'
        topCgiLogString = config.siteInfo['CgiHtmlPath']+'buildlogs/'+pathReq.split('/')[1]+'/'+ib+'/pyRelValMatrixLogs/run'

        self.formatter.writeH3('Integration Build ' + ib + backToPortal)

        (rvCmds,stepsCount) = getRVCmds.getCmds(normPath)
        if stepsCount == 0:
            self.formatter.writeH3("Test logs not yet available")
            return

        passed, failed, timeout, notrun, stepOK, stepFail = self.getSummaryLogInfo(normPath, stepsCount)

        if stepOK['step1']==0 and stepFail['step1']==0:
            self.formatter.writeH3("Test logs not yet available")
            return

        steps = []
        for i in range(1,stepsCount+1): steps.append('step'+str(i))

        self.formatter.startTable ( [15,15,15,15,15,15], ['Step','total', 'passed', 'failed', 'timeout', 'notRun'])
        tFailed = 0 ; tTimeOut = 0
        for step in steps:
          nPass = len(passed[step])
          nFail = len(failed[step])
          nTime = len(timeout[step])
          nNotRun= len(notrun[step])
          tFailed += nFail
          tTimeOut += nTime
          self.formatter.writeRow([step  , str(nPass+nFail+nTime), str(nPass), str(nFail), str(nTime), str(nNotRun)])

        comparison_passed, comparison_failed, comparison_timeout, comparison_notrun, comparison_stepOK, comparison_stepFail, report_path, report_status = self.getBuildComparisonLogInfo(normPath)
        nCompPass = len(comparison_passed)
        nCompFail = len(comparison_failed)
        nCompTime = len(comparison_timeout)
        nCompNotRun1= len(comparison_notrun)
        self.formatter.writeRow(['Comparison'  , str( nCompPass + nCompFail + nCompTime + nCompNotRun1 ), str( nCompPass ), str( nCompFail ), str( nCompTime ), str(nCompNotRun1) ])
        self.formatter.endTable()

        for log in glob(normPath+'/runall.log*'):
	  log = os.path.basename(log)
          self.formatter.writeH3('<a href="'+logBaseURL+pathReq+'/'+log+'"> Summary log ('+log+') </a>')

        self.formatter.showLine()

        msgFail = '<a> Failed tests : ('+str(tFailed)+') '
        msgFail += '</a> <br />'
        self.formatter.writeH3(msgFail + ' <a href="#top"> back to top </a> ')

        logFileMap = self.getLogFiles(normPath)

        if tTimeOut > 0:
            msgTime = '<a name="timedOut"> Timed out tests : ('+str(tTimeOut)+') '
            msgTime += '</a>'
            self.formatter.writeH3(msgTime + ' <a href="#top"> back to top </a> ')

            for step in steps:
                for lineIn in timeout[step]:
                    line = lineIn.replace("'",'').replace('"','').replace('/', '_')
                    stepId = step+'_'+line
                    outLine = ''
                    try:
                        outLine = '<a href="'+topCgiLogString+'/'+logFileMap[stepId]+'"> '+stepId+' </a>'
                    except KeyError:
                        outLine = stepId
                    try:
                        outLine += '<br/><font size="-1">  '+rvCmds[line][step]+'</font>'
                    except KeyError:
                        outLine += '<br/><font size="-1">  Unknown Command</font>'
                    self.formatter.write(outLine +'<br /><br />')

        self.formatter.writeH3('<a name="tests"> RelVal tests: ('+str(len(passed['step1']))+' tests) </a> <br /> <a href="#top"> back to top </a> ')

        rows = {}
        styles = {}
        orderedKeys = []
        for step in steps:
            styleClass = "failed"
            for lineIn in failed[step] :
                line = lineIn.replace("'",'').replace('"','').replace('/','_')
                line = line.replace("'",'').replace('"','')
                stepId = step+'_'+line
                outLine = ''
                index = stepId
                try: index = logFileMap[stepId]
                except KeyError: pass
                outLine = '<a href="'+topCgiLogString+'/'+index+'">'
                outLine += 'log</a>&nbsp;&nbsp;<a class="detail" name="'+stepId+'" onclick="showHide(this) ">cmd</a> <a class="info" name="'+stepId+'" onclick="showHide(this) ">hide<br/>'
                try:
                    outLine += '<br/><font size="-1" color="black">'+rvCmds[line][step]+'</font>'
                except KeyError:
                    outLine += '<br/><font size="-1" color="black"> no info found :( </font>'
                outLine += "</a>"

                index = line
                if index not in rows.keys():
                    rows[index] = {}
                    styles[index] = {}
                rows[index][step] = outLine 
                styles[index][step] = styleClass 
                if index not in orderedKeys: orderedKeys.append(index)

        for step in steps:
            styleClass = "passed"
            for lineIn in passed[step] :
                line = lineIn.replace("'",'').replace('"','').replace('/','_')
                line = line.replace("'",'').replace('"','')
                stepId = step+'_'+line
                index = stepId
                try: index = logFileMap[stepId]
                except KeyError: pass
                outLine = '<a href="'+topCgiLogString+'/'+index+'">'
                outLine += 'log</a>&nbsp;&nbsp;<a class="detail" name="'+stepId+'" onclick="showHide(this) ">cmd</a> <a class="info" name="'+stepId+'" onclick="showHide(this) ">hide<br/>'
                try:
                    outLine += '<br/><font size="-1" color="black">'+rvCmds[line][step]+'</font>'
                except:
                    outLine += '<br/><font size="-1" color="black"> N/A </font>'
                outLine += "</a>"

		index = line
                if index not in rows.keys():
                    rows[index] = {}
                    styles[index] = {}
                rows[index][step] = outLine 
                styles[index][step] = styleClass 
                if index not in orderedKeys: orderedKeys.append(index)

        sSize = [15]
        for s in range(0,stepsCount): sSize.append(15)                        
        self.formatter.startTable( [10, 30] + sSize, ['#', 'workflow']+steps+['Comparison'])
        num = 0
        wfre = re.compile("^(\d+\.\d+)_([^+]+)(\+|)(.*)$")
        self.readLogMessageInfo(normPath)
        for sample in orderedKeys:
            num += 1
            row = [ str(num) ]
            rowStyles = ['']
            style = "passed"
            rdata = sample
            for x in styles[sample]:
                if styles[sample][x] == "failed":
                    style = "failed"
                    break
            m = wfre.match(sample)
            if m:
                wf = m.group(1)
                wftype = m.group(2)
                wfseq = m.group(4)
                if wfseq != "":
                    wfseq += '</br>'
                rdata = '<a class="detail" name="'+wf+'" onclick="showHide(this) ">'+wf+'  '+wftype+'</a><a class="info" name="'+wf+'" onclick="showHide(this) ">hide<br/>'
                rdata += wf+'  '+wftype+'</br>'+wfseq+'cmd: runTheMatrix.py -l '+wf+'</br></a>'
            row.append( rdata )
            rowStyles.append('"'+style+' '+'left"')
	    for xstep in range(0,stepsCount+1):
                if xstep == stepsCount:
                    if report_path.has_key(sample):
                        class_passed = 'passed'
                        class_failed = 'failed'
                        report_notrun = 'notrun'
                        report_compilation_status = class_passed
                        report_class = report_status[sample]
                        if report_class == report_notrun:
                            report_class = class_failed
                            report_compilation_status = class_failed
                        extraStr  = '<table border="0" cellspacing=2 cellpadding=2><tr>'
                        extraStr += '<td class=' + report_class + '> &nbsp; </td>'
                        extraStr += '<td class=' + report_compilation_status + '> &nbsp; </td>'
                        extraStr += '<td><a href="' + (DQMReportsBaseURL + str(report_path[sample])) + '">report</a></td></tr></table>'
                        row.append(extraStr)
                        rowStyles.append( '' )
                    else:
                        row.append( '&nbsp;' )
                        rowStyles.append( '' )
                else:  
                    step = 'step'+str(xstep+1)
                    try:
                        wfInfo  = rows[sample][step]
                        warnMsg = 'passed'
                        errMsg  = 'passed'
                        try:
                            events = self.LogMessages[wf]['events'][xstep]
                            if events>0:
                                if self.LogMessages[wf]['failed'][xstep]/float(events)  > 0.05: errMsg   = 'failed'
                                if self.LogMessages[wf]['warning'][xstep]/float(events) > 0.1:  warnMsg  = 'failed'
                        except:
                            pass
                        extraStr  = '<table border="0" cellspacing=2 cellpadding=2><tr>'
                        extraStr += '<td class='+styles[sample][step]+'> &nbsp; </td>'
                        extraStr += '<td class='+errMsg+'> &nbsp; </td>'
                        extraStr += '<td class='+warnMsg+'> &nbsp; </td>'
                        extraStr += '<td>'+wfInfo+'</td></tr></table>'
                        row.append(extraStr)
                        rowStyles.append( '' )
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

    fmtr = Formatter.SimpleHTMLFormatter(title="Test Logs from CMSSW Integration Build", style=style)

    lv = LogViewer(fmtr)
    lv.showLogs()

    return


main()
