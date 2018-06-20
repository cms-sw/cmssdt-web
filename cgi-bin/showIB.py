#!/usr/bin/env python

# make sure this is first to trap also problems in includes later
import cgitb; cgitb.enable() ## cgitb.enable(display=0, logdir=os.getcwd()+"/../cgi-logs/")

import os, sys, cgi, time, re

from pickle import Unpickler
from glob import glob

# scriptPath = '/afs/cern.ch/cms/sdt/web/cgi-bin/'
# if scriptPath not in sys.path:
#     sys.path.append(scriptPath)

import Formatter

import config

def blistCmp(a,b):
    if b[2]==a[2]: return cmp(b[1], a[1])
    return cmp(b[2], a[2])

class BuildViewer(object):

    def __init__(self, formatter):

        self.formatter = formatter
        
        self.buildList = {}
        self.platCycleMap = {}
        from helpers import archList,activeReleaseCycles
        self.platList = archList
        
        self.webLogDirBase = config.siteInfo['afsPath']
        self.webLogDir = None # to be set up as base+plat+'/www/'
        
        self.webLogURLBase = config.siteInfo['HtmlPath']+'/rc/'
        self.webLogCGIBase = config.siteInfo['CgiHtmlPath']

        self.dayList = [ 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun' ]
        self.dayMap = { 'mon':0, 'tue':1, 'wed':2, 'thu':3, 'fri':4, 'sat':5, 'sun':6 }

        self.cycList = activeReleaseCycles

        return

    # --------------------------------------------------------------------------------

    def days(self,today):

        index = self.dayMap[today]

        days = []
        for i in range(index,-1,-1):
            days.append(self.dayList[i])

        for i in range(len(self.dayList)-1,index,-1) :
            days.append(self.dayList[i])
        
        return days

    # --------------------------------------------------------------------------------

    def getListOfBuilds(self):

        import datetime

        form = cgi.FieldStorage()
        rc = None
        if form.has_key('rc'):
          rc = form['rc'].value
          if rc in self.cycList: self.cycList = [ rc ]
          else: rc=None

        # only list the builds with the "canonical" naming structure ... 
        buildRe = re.compile('^CMSSW_(\d+_\d+)(|_.+)_X_(.+_|)(\d\d\d\d-\d\d-\d\d)-(\d\d)\d\d$')

        for plat in self.platList:
            self.platCycleMap[plat] = []
            for day in self.dayList:
                self.webLogDir = os.path.join(self.webLogDirBase, plat, 'www')
                dayIndex = day+'/'+plat
                self.buildList[dayIndex] = []
                entries = []
                try:
                    if rc: entries = glob( os.path.join(self.webLogDir,day,rc+'-'+day+'-*') )
                    else:  entries = glob( os.path.join(self.webLogDir,day,'*-'+day+'-*') )
                except OSError:
                    pass
                except Exception, e:
                    self.formatter.write("ERROR reading dir for "+day + str(e) +'\n')
                for entry in entries:
                    builds = list(os.listdir(entry))
                    for build in builds:
                        buildMatch = buildRe.match(build)
                        if buildMatch:
                            cyc   = buildMatch.group(1).replace('_','.')
                            bDate  = buildMatch.group(4)
                            hr    = buildMatch.group(5)
                            y,m,d = bDate.split('-')
                            age   = (datetime.date.today() - datetime.date(int(y),int(m),int(d))).days
                            if age > 6 : continue
                            self.buildList[dayIndex].append( [ os.path.basename(entry), build, cyc+'-'+hr ] )
                            cyc = cyc + '.' + build
                            if cyc not in self.platCycleMap[plat]:
                                self.platCycleMap[plat].append( cyc )

	return

    # --------------------------------------------------------------------------------

    def isEmpty(self, day, bDir, build, subDir):

        ret = False
        try:
            chkDir = os.path.join(self.webLogDir, day, bDir, build, subDir)
            entries = os.listdir(chkDir)
            ret = len(entries) == 0
        except:
            pass
        
        return ret

    # --------------------------------------------------------------------------------

    def getValgrindErrors(self, ib, arch):

        import helpers
        return helpers.getValgrindErrors(ib, arch)

    # --------------------------------------------------------------------------------

    def exists(self, day, bDir, build, subDir, file):

        ret = False
        try:
            chkDir = os.path.join(self.webLogDir, day, bDir, build, subDir)
            entries = os.listdir(chkDir)
            if file in entries: ret = True
        except:
            pass
        
        return ret

    # --------------------------------------------------------------------------------
    
    def getBuildInfo(self, bldLogFileName):

        info = None
        bldClassStyle = None
        tstClassStyle = None
        if not os.path.exists(bldLogFileName):
            return info, bldClassStyle, tstClassStyle

        log = open(bldLogFileName, 'r')
        lines = log.readlines()
        log.close()
        
        # new/index.html
        # <tr class="dictErr"> <td>dictError </td><td> 0</td><td> 0</td></tr>
        # <tr class="compErr"> <td>compError </td><td> 0</td><td> 0</td></tr>
        # <tr class="linkErr"> <td>linkError </td><td> 0</td><td> 0</td></tr>
        # <tr class="pyErr"> <td>pythonError </td><td> 26</td><td> 115</td></tr>
        # <tr class="compWarn"> <td>compWarning </td><td> 187</td><td> 2546</td></tr>
        # <tr class="dwnldErr"> <td>dwnlError </td><td> 0</td><td> 0</td></tr>
        # <tr class="miscErr"> <td>miscError </td><td> 0</td><td> 0</td></tr>

        items = ['dictError', 'compError', 'linkError', 'pythonError',
                 'compWarning', 'dwnlError', 'miscError', 'unitTestErrors', 'depViolations' ]

        reInfoRe = {}
        for item in items:
            reInfoRe[item] = re.compile(r'.*<td>'+item+'\s*</td><td>\s*(\d+)\s*</td>.*')


        wwwDir = os.path.dirname(bldLogFileName).replace('/new','')
	othErr, errs = self.getOtherBuildInfo( wwwDir.replace('www/',''),wwwDir)
        for line in lines:
            for item in items:
                reInfoMatch = reInfoRe[item].match(line)
                if reInfoMatch :
                    errs[item] = int(reInfoMatch.group(1))
            if 'subsystem/package' in line : break # enough read ;)

        if errs:
            if ( errs['compWarning'] > 0) :bldClassStyle = 'warning'

            useOtherTests = True
            if ( 'CMSSW_3_8_' in bldLogFileName or
                 'CMSSW_3_9_' in bldLogFileName ) : useOtherTests = False

            if useOtherTests:
                tstClassStyle = 'passed'
                if (errs['unitTestErrs']>0)  or (errs['depViolations']>0): tstClassStyle = 'failed'
                elif (errs['unitTestErrs']<0)  or (errs['depViolations']<0): tstClassStyle = 'unknown'                

            if ( errs['dictError']   > 0 or
                 errs['compError']   > 0 or
                 errs['linkError']   > 0 or
                 errs['miscError']   > 0 or
                 errs['dwnlError']   > 0 
                 ) :
                bldClassStyle = 'failed'

            if ( (errs['pythonError'] > 0) and bldClassStyle != 'failed' ): # check this only if it's not yet "failed"
                bldClassStyle = 'failed'

        if not bldClassStyle: bldClassStyle='passed'
        return errs, bldClassStyle, tstClassStyle

    # --------------------------------------------------------------------------------
    
    def mkErrString(self, bErr):
        
        errorKeys = ['dictError',
                     'compError',
                     'linkError',
                     'pythonError',
                     'compWarning',
                     'dwnlError',
                     'miscError',
                     'unitTestErrs',
                     'depViolations',
                         ]
        errString = ""
        for k in errorKeys:
            try:
                v = bErr[k]
            except:
                errString = 'N/A'
            else:
                col = 'red'
                if 'Warning' in k: col='orange'
                if v == 0: col = 'green'
                errString += "<font color="+col+">%s : %s </font><br />" % (k.replace("Warning",'Warn').replace('onError','onErr'),v)

        return errString

    # --------------------------------------------------------------------------------
    
    def getRVInfo(self, rvLogDir, build, plat):
        import pickle
        summDir = config.siteInfo['OutPath']+'/'+build+'/'+plat
        summPath = summDir+'/pyRelValsSummary.pkl'
        data = None
        if os.path.exists(summPath) and (os.stat(summDir).st_mtime <= os.stat(summPath).st_mtime):
            try:
                data = pickle.load( open(summPath,'r') )
            except:
                pass
            return data

        logErrs = 0
        logWarns = 0
        for rvLogFileName in glob(rvLogDir+'/runTheMatrixMsgs.pkl*'):
            try:
              logData = pickle.load( open(rvLogFileName,'r') )
              for wf in logData.keys():
                for x in range(0,4):
                  evt = logData[wf]['events'][x]
                  if evt>0:
                    if (logData[wf]['failed'][x]/float(evt)  > 0.05): logErrs  += 1
                    if (logData[wf]['warning'][x]/float(evt) > 0.1):  logWarns += 1
            except:
              return data

        timeoutRe = re.compile('ERROR executing .*? cd (\d+.*)\; cmsDriver.py .*? ret= (\d+)')
        totP = 0
        totF = 0
        nTimeOut = 0
	hasLog = False
	for rvLogFileName in glob(rvLogDir+'/runall.log*'):
          hasLog = True
          rvLog = open(rvLogFileName, 'r')
          lines = rvLog.readlines()
          rvLog.close()

          for line in lines:
            timeoutMatch = timeoutRe.match(line)
            if timeoutMatch:
                workflow, ret = timeoutMatch.groups()
                if int(ret.strip()) == 36608 :
                    nTimeOut += 1
                
            if 'tests passed' not in line: continue
            regex = re.compile('^\s*((\d+\s+)+)tests passed.*?((\d+\s+)+)failed\s*$')
            m = regex.match(line)
            if m:
                for x in m.group(1).strip().split(): totP += int(x)
		for x in m.group(3).strip().split(): totF += int(x)
                
        if not hasLog: return data
        totF = totF-nTimeOut
        data = [totP, totF, nTimeOut, logErrs, logWarns]

        from pickle import Pickler
        try:
            outFile = open(summPath, 'w')
            pklFile = Pickler(outFile)
            pklFile.dump(data)
            outFile.close()
        except:
            pass

        return data

    # --------------------------------------------------------------------------------
    
    def getBuildComparisonLogStyles(self, path):
        compilationStatus = 0
        statisticalStatus = 0
        passed            = 0
        logRe = re.compile('\s*(\w.*?)\s*Comparison-([PNF].*?)\s*report:\s*([a-zA-Z0-9/_//./-]*)')
        for logFileName in glob(path+"/runall-comparison.log*"):
          lines = []
          try:
              sumLog = open(logFileName, 'r')
              lines += sumLog.readlines()
              sumLog.close()
          except:
              pass        
          if len(lines)==0: return -1, -1, -1

          for line in lines:
            logMatch = logRe.match(line)
            if logMatch:
                job = logMatch.group(1)
                sample = job.replace(' ','_')
                comparisonRes = logMatch.group(2)

                if 'NOTRUN' in comparisonRes:
                    compilationStatus += 1
                    statisticalStatus += 1
                elif 'FAILED' in comparisonRes:
                    statisticalStatus += 1
		else: passed +=1

        return statisticalStatus, compilationStatus, passed

    def getAddOnInfo(self, logFileName):

        info = None
        if not os.path.exists(logFileName):
            return info

        rvLog = open(logFileName, 'r')
        lines = rvLog.readlines()
        rvLog.close()

        passed = 0
        failed = 0

        logRe = re.compile('(cmsRun|cmsDriver.py)\s+(.*?)\s:\s([PF].*?D)\s.*')

        for line in lines:

            logMatch = logRe.match(line)
            if logMatch:
                runOrDriver = logMatch.group(1)
                cmd = logMatch.group(2).replace('_',' ')
                res = logMatch.group(3)

                if 'PASSED' in res:
                    passed += 1
                elif 'FAILED' in res:
                    failed += 1

        return passed, failed

    # --------------------------------------------------------------------------------
    
    def refreshQASummary(self, build, day, plat):
        import urllib2
        qaSummPageURL = self.webLogCGIBase+'newQA.py?'
        qaSummPageURL += 'arch='+plat+'&release='+build+'&summaryOnly=1'

        page = urllib2.urlopen(qaSummPageURL)
        lines = page.readlines()
        page.close()

        return
    # --------------------------------------------------------------------------------
    
    def getQASummary(self, build, day, plat):

        allDone, vgErrs, igErrs, cfgErr, ddErr, dfsErr, crcErr, prodErr, fwliteErr, onlineErr = self.readQASummary(build, day, plat)
        # check if a refresh is needed ...
        if not allDone:
            self.refreshQASummary(build, day, plat)
            allDone, vgErrs, igErrs, cfgErr, ddErr, dfsErr, crcErr, prodErr, fwliteErr, onlineErr = self.readQASummary(build, day, plat)

        return vgErrs, igErrs, cfgErr, ddErr, dfsErr, crcErr, prodErr, fwliteErr, onlineErr

    # --------------------------------------------------------------------------------
    
    def readQASummary(self, build, day, plat):

        summPath = config.siteInfo['OutPath']+'/'+build+'/'+plat
        try:
            summFile = open(summPath+'/qaSummary.pkl', 'r')
        except IOError:
            # print "ERROR opening qaSummary pkl file "+summPath+'/qaSummary.pkl'+"<br/>"
            return [False, -1,-1,-1,-1,-1,-1,-1,-1,-1]
        
        pklr = Unpickler(summFile)
        vgErrs  = int( pklr.load() )
        igErrs  = int( pklr.load() )
        ddErr   = pklr.load()
        cfgInfo = pklr.load()
        allDone = pklr.load()
        try:
            dfsErr = pklr.load()
            if type(dfsErr) == type ( (0,1) ):
                dfsErr = dfsErr[0]+dfsErr[1]
        except EOFError:
            dfsErr = -1
        try:
            prodErr  = int( pklr.load() )
        except EOFError:
            prodErr = -1
        try:
            fwliteErr  = int( pklr.load() )
        except EOFError:
            fwliteErr = -1
        try:
            onlineErr  = int( pklr.load() )
        except EOFError:
            onlineErr = -1
        summFile.close()

        cfgErr = 0
        if cfgInfo[1] : cfgErr = len(cfgInfo[1])

        # summary from the code rule checks
        ruleErrs = -1
        import helpers
        wkDay, stamp, cycle = helpers.getStamp(build)
        crcSummPath = os.path.join(config.siteInfo['afsPath'], plat, 'www', day, cycle.replace('_','.')+'-'+stamp, build, 'codeRules' )
        import glob
        gotInfo = False
        for crcFile in glob.glob(crcSummPath+'/cmsCodeRule*.dat'):
            try:
                crcSummFile = open(crcFile, 'r')
                pklr = Unpickler(crcSummFile)
                ruleErrs += len( pklr.load().keys() )
                gotInfo = True
                crcSummFile.close()
            except:
                # self.formatter.write( "ERROR opening crcSummary pkl file "+crcSummPath+'/qaSummary.pkl'+"<br/>")
                ruleErrs = -1
                gotInfo = False
                break

        if not gotInfo:
            # self.formatter.write("did not get info ... " + str(ruleErrs) )
            ruleErrs = -1
        
        return [allDone, vgErrs, igErrs, cfgErr, ddErr[0], dfsErr, ruleErrs, prodErr, fwliteErr, onlineErr]

    # --------------------------------------------------------------------------------

    def findAllBuilds(self, rc, day):

        rx = re.compile(rc+"(|.+)-"+day)
        listOfBuilds = []
        for key,bLists in self.buildList.items():
            bLists.sort(blistCmp)
            for bList in bLists:
                # print rc+'-'+day, day, key, bList,'<br />'
                if rx.match(bList[0]):
                    # print 'found  ', rc+'-'+day, day, bList,'<br />'
                    if (bList[0],bList[1],bList[2]) not in listOfBuilds:
                        # print 'adding', rc+'-'+day, day, bList,'<br />'
                        listOfBuilds.insert(0, (bList[0], bList[1], bList[2] ) )

        # make sure the builds are sorted (by the first arg: timeStamp)
        listOfBuilds.sort(blistCmp)
        return listOfBuilds

    # --------------------------------------------------------------------------------

    def readPklFile(self, fileName,OnlyErrors=False ):

        summFile = ""
        try:
            summFile = open(fileName, 'r')
        except IOError:
            # print "ERROR opening ",bDir + '/unitTestResults.pkl'
            return None, None
        
        pklr = Unpickler(summFile)
        utErrs = pklr.load()        
        summFile.close()

        partErrs = 0
        if OnlyErrors:
            for pkg, res in utErrs.items():
                partErrs += res
        else:
            for pkg, res in utErrs.items():
                tstList, nOK, nErr = res
                partErrs += nErr

        return partErrs

    # --------------------------------------------------------------------------------

    def getOtherBuildInfo(self, bDir, wwwDir):

        sumErr = 0
        obi = {}

        try:
            xFile = bDir + '/unitTestResults.pkl'
	    if os.path.exists(wwwDir + '/unitTestResults.pkl'): xFile = wwwDir + '/unitTestResults.pkl'
	    partErrs = self.readPklFile(xFile)
            sumErr += partErrs
            obi['unitTestErrs'] = partErrs
        except:
            obi['unitTestErrs'] = -1
            pass

        try:
            xFile =bDir + '/testLogs/depViolationSummary.pkl'
            if os.path.exists(wwwDir + '/testLogs/depViolationSummary.pkl'): xFile = wwwDir + '/testLogs/depViolationSummary.pkl'
            partErrs = self.readPklFile(xFile,True)
            sumErr += partErrs
            obi['depViolations'] = partErrs
        except:
            obi['depViolations'] = -1
            pass

        return  sumErr, obi

    # --------------------------------------------------------------------------------
    
    def hasNote(self, bDir):
        rcNoteName = bDir+'/rcNotes.txt'
        if not os.path.exists(rcNoteName):
            return ""
        else:
            rcN = open(rcNoteName,'r')
            lines = rcN.readlines()
            rcN.close()
            return ' '.join(lines)

    # --------------------------------------------------------------------------------
    
    def showBuilds(self):

        self.formatter.writeAnchor(ref='top')
        self.formatter.writeH2('<a href="'+self.webLogCGIBase+'showIB.py">CMSSW integration builds</a>')

        msg = """

<p>
Click on the "summary" links to get some summary information for the build status and/or relval status.
</p>
<p>
Click on the alert icon (%s) to see information provided by the release manager for that specific IB.
</p>

""" % ('<img src="'+self.webLogURLBase.replace('/rc/','')+'icons/alert.red.png" alt="alert" />',)

        self.formatter.write(msg)

        colFmt = [   10,   20,          20,       20,         30 ,           30,       30 ]
        colLab = ['day', 'IB', 'platforms', 'builds', 'RelVals', 'OtherTests','Q/A page' ]
        
        today = time.strftime('%a').lower()

        afsBaseDir = '/data/sdt/buildlogs/'
        isDevel = True
        
        for rc in self.cycList:

            self.formatter.writeAnchor(ref=rc)
            self.formatter.writeH3("Release cycle "+rc+ '  -- <a href="#top">back to top of page</a>')
            if isDevel:
              self.formatter.writeH3("<a href='https://cmssdt.cern.ch/SDT/jenkins-artifacts/performance/summary/performanceSummaryOut.html'>Historical performance plots.</a>")
              isDevel = False
            self.formatter.startTable(colFmt, colLab, cls='mainTable')

            dayCount = 0
            rowStyle = ''
            hiddenStarted = False
            for day in self.days(today):
                dayCount += 1
                if dayCount > 3 and not hiddenStarted:
                    hiddenStarted = True
                    # self.formatter.writeRow(['','<a class="showOld" name="'+rc+'" onclick=toggleIBs(this) "> show older IBs </a>','','','','',''])
                    # rowStyle = 'class="oldIB" name="'+rc+'" style="display:none;" '
                    self.formatter.write('</table>')
                    self.formatter.write('<div class="showOld"><a class="showOld" name="'+rc+'" onclick=toggleIBs(this) "> show older IBs </a></div>')
                    self.formatter.write('<table border="1" class="oldIB" name="'+rc+'" style="display:none;" >')

                bold = False
                # if day == today:
                #    bold = True

                    
                builds = self.findAllBuilds(rc, day)
                
                for item in builds:

                    qaPage = 'N/A'
                    bldTable = '<table border="0" cellspacing=0 cellpadding=2 class="bldTable"><tr> \n'
                    rvTable  = '<table border="0" cellspacing=0 cellpadding=2 class="rvTable" ><tr> \n'
                    aoTable  = '<table border="0" cellspacing=0 cellpadding=2 class="aoTable" ><tr> \n'
                    qaTable  = '<table border="0" cellspacing=0 cellpadding=2 class="qaTable" ><tr> \n'
                    colCount = 0
                    platCol = '<table>\n'
                    for plat in self.platList:
                    
                        bDir, build, xcyc = item
                        if rc+'.'+build not in self.platCycleMap[plat] : continue

                        dayIndex = day+'/'+plat
                        relCyc, stamp = bDir.split('-', 1)
                      
                        #if rc not in self.platCycleMap[plat] :
                            # print 'no rc in platCycleMap found <br />'
                            #continue

                        self.webLogDir = os.path.join(self.webLogDirBase, plat, 'www')
                        relBaseDir = plat+'/www/'+day+'/'+bDir+'/'+build+'/'

                        rcNote = self.hasNote(afsBaseDir+relBaseDir.replace('/'+build,''))
                        rcNoteInfo = ''
                        rcNoteDetails = ''
                        if rcNote != "":
                            rcNoteInfo    = '<a class="detail" name="'+bDir+'_'+plat+'" onclick=showHide(this) "><img src="'+self.webLogURLBase.replace('/rc/','')+'icons/alert.red.png" alt="alert" /></a>'
                            rcNoteDetails = '<a class="info"   name="'+bDir+'_'+plat+'" onclick=showHide(this) "> hide:<br/> '+rcNote+' </a>'

                        platCol += '<tr><td> '+rcNoteDetails+'&nbsp;'+rcNoteInfo+plat+'&nbsp;'+'</td></tr>\n'
                            

                        # ------------------------------------------
                      
                        bldLogFileName = afsBaseDir + relBaseDir + 'new/index.html'
                        bErr,bStyle,tStyle = self.getBuildInfo(bldLogFileName)
                      
                        bldClassStyle = 'neutral'
                        if bold:
                            bldClassStyle = 'cellbold'
                        if bStyle : bldClassStyle = bStyle

                        tstClassStyle = 'unknown'
                        if bold:
                            tstClassStyle = 'cellbold'
                        if tStyle : tstClassStyle = tStyle

                        detailId = 'bld_'+day+build+plat
                        info = "hide summary <br/> " + self.mkErrString(bErr)

                        bldSumm    = '<a class="'+bldClassStyle+'"> &nbsp; </a>'
                        tstSumm    = '<a class="'+tstClassStyle+'"> &nbsp;</a>'
                        bldDetails = '<a class="detail" name="'+detailId+'" onclick="showHide(this) "> summary </a>'
                        bldInfo    = '<a class="info"   name="'+detailId+'" onclick="showHide(this) "> '+info+' </a>'

                        pklFile = afsBaseDir+relBaseDir+'new/logAnalysis.pkl'
                        if os.path.exists(pklFile):
                            buildLink = '<a href="'+self.webLogCGIBase + 'showBuildLogs.py/'
                            buildLink += relBaseDir
                            buildLink += '"> details </a>'
                        else:
                            buildBase = '<a href="'+self.webLogURLBase+relBaseDir
                            buildLink = buildBase + '/new"> details </a>'
                        # ------------------------------------------
                      
                        rvAfsDir = afsBaseDir + relBaseDir + '/pyRelValMatrixLogs/run/'
                        rvInfoStr = self.getRVInfo(rvAfsDir,build,plat)
                        rvClassStyle  = 'neutral'
                        rvClassErr    = 'unknown'
                        rvClassWarn   = 'unknown'
                        if bold:
                            rvClassStyle = 'cellbold'
                        if rvInfoStr :
                            if rvInfoStr[0] > 0 :    rvClassStyle = 'passed'
                            if rvInfoStr[1] > 0 :    rvClassStyle = 'failed'
                            if rvInfoStr[2] > 0 :    rvClassStyle = 'failed'
                            if rvInfoStr[3] > 0 :    rvClassErr   = 'failed'
                            elif rvInfoStr[3] == 0 : rvClassErr   = 'passed'
                            if rvInfoStr[4] > 0 :    rvClassWarn  = 'failed'
                            elif rvInfoStr[4] == 0 : rvClassWarn   = 'passed'

                        detailId = 'rv_'+day+build+plat
                        rvSumm    = '<a class="'+rvClassStyle+'"> &nbsp; </a>&nbsp;<a class="'+rvClassErr+'"> &nbsp;</a>&nbsp;<a class="'+rvClassWarn+'"> &nbsp;</a>'
                        statErr, compilationErr, compPassed  = self.getBuildComparisonLogStyles(rvAfsDir)
			rvCmpStatErrClassStyle = 'unknown'; rvCmpCompilationErrClassStyle='unknown'
			if statErr==0: rvCmpStatErrClassStyle='passed'
			elif statErr>0: rvCmpStatErrClassStyle='failed'
			if compilationErr==0: rvCmpCompilationErrClassStyle='passed'
			elif compilationErr>0: rvCmpCompilationErrClassStyle='failed'
			
                        infoStr = "hide summary <br/> " + '<font color=green>%s RVs passed </font><br/><font color=red>%s RVs failed</font><br/><font color=orange>%s RVs timed out</font><br/>'
                        infoStr+= "<font color=red>%s Error msgs</font><br/><font color=red>%s Warnings msgs</font><br/>"
                        infoStr+= "<font color=green>%s DQM passed </font><br/><font color=red>%s DQM stat. errs</font><br/><font color=red>%s DQM compilation errs</font>"
                        try:
                            info = infoStr % (rvInfoStr[0], rvInfoStr[1], rvInfoStr[2], rvInfoStr[3], rvInfoStr[4], compPassed, statErr, compilationErr)
                        except:
                            info = "hide summary <br /> " + 'unknown RVs passed; unknown RVs failed'

                        rvCmpSumm    = '<a class="'+rvCmpStatErrClassStyle+'"> &nbsp;</a>&nbsp;<a class="'+rvCmpCompilationErrClassStyle+'"> &nbsp;</a>'
                        rvDetails = '<a class="detail" name="'+detailId+'" onclick="showHide(this) "> summary </a>'
                        rvInfo    = '<a class="info"   name="'+detailId+'" onclick="showHide(this) "> '+info+' </a>'

                        pyRelValLogs = '<a href="'+self.webLogCGIBase + '/showMatrixTestLogs.py/'
                        pyRelValLogs += plat+'/www/'+day+'/'+bDir+'/'+build
                        pyRelValLogs += '/pyRelValMatrixLogs/run/"> details </a>'
                        if ( self.isEmpty(day, bDir, build, 'pyRelValMatrixLogs/run') or
                             ('unknown RVs passed' in info and 'unknown RVs failed' in info) ):
                           pyRelValLogs = ' no info available '

                        # ------------------------------------------
                      
                        aoAfsDir = afsBaseDir + relBaseDir + '/addOnTests/logs/'
                        aoInfoStr = self.getAddOnInfo(aoAfsDir+'../../addOnTests.log')
                        aoClassStyle = 'neutral'
                        if bold:
                            aoClassStyle = 'cellbold'
                        if aoInfoStr :
                            if aoInfoStr[0] > 0 : aoClassStyle = 'passed'
                            if aoInfoStr[1] > 0 : aoClassStyle = 'failed'

                        detailId = 'ao_'+day+build+plat
                        infoStr = "hide summary <br/> "
                        infoStr += '<font color=green>%s AOs passed </font><br /><font color=red>%s AOs failed</font>'
                        try:
                            info = infoStr % (aoInfoStr[0], aoInfoStr[1])
                        except:
                            info = "hide summary <br/> " + 'unknown AOs passed; unknown AOs failed'
                        
                        aoSumm    = '<a class="'+aoClassStyle+'" > &nbsp; </a>'
                        aoDetails = '<a class="detail" name="'+detailId+'" onclick="showHide(this) "> summary </a>'
                        aoInfo    = '<a class="info"   name="'+detailId+'" onclick="showHide(this) "> '+info+' </a>'
                        addOnLogs = '<a href="'+self.webLogCGIBase + '/showAddOnLogs.py/'
                        addOnLogs += plat+'/www/'+day+'/'+bDir+'/'+build
                        addOnLogs += '/addOnTests/"> details </a>'
                        if ( self.isEmpty(day, bDir, build, '/addOnTests/logs') or
                             ('unknown AOs passed' in info and 'unknown AOs failed' in info) ):
                           addOnLogs = ' no info available '

                        # ------------------------------------------
                      
                        errSum = self.getQASummary(build, day, plat)
                        qaSumSubTbl = '<table border="0" cellspacing=2 cellpadding=2 class="qaSumTable"><tr> \n'
			xcount = 0
                        names = [ "valgrind", "ignominy", "old cfg files", "duplicate dictionary", "dir/file size", "code rules", "prod workflow", "fwlite", "online" ]
                        for qaItem in errSum:
			    xcount+=1
                            qaItemStyle = 'passed'
                            qaItemCnt = int(qaItem)
                            if qaItemCnt < 0 : qaItemStyle = 'unknown'
                            elif qaItemCnt > 0:
                                qaItemStyle = 'failed'
                                if (xcount == 8) or (xcount == 9):
                                    if (qaItemCnt==1): qaItemStyle = 'warning'
                                    elif (qaItemCnt==3): qaItemStyle = 'skipped'
                            qaSumSubTbl += '<td class="'+qaItemStyle+'" title="'+names[xcount-1]+'"> &nbsp; </td>'

                        qaPage = '<td> <a href="'+self.webLogCGIBase+'/newQA.py?'
                        qaPage += 'arch='+plat+'&release='+build
                        qaPage += '"> Q/A info</a> </td>'
                        if os.path.exists(os.path.join("/data/sdt/SDT/jenkins-artifacts/ib-static-analysis", build, plat)):
                          qaPage += '<td>'
                          qaPage += '<a href="https://cmssdt.cern.ch/SDT/jenkins-artifacts/ib-static-analysis/'+ build + '/' + plat + '/llvm-analysis">Static Analyzer</a><br>'
                          qaPage += '<a href="https://cmssdt.cern.ch/SDT/jenkins-artifacts/ib-static-analysis/'+ build + '/' + plat + '/reports/modules2statics.txt">Modules to thread unsafe statics</a><br>'
                          qaPage += '<a href="https://cmssdt.cern.ch/SDT/jenkins-artifacts/ib-static-analysis/'+ build + '/' + plat + '/reports/tlf2esd.txt">Modules to thread unsafe EventSetup products</a><br>'
                          qaPage += '</td>'
                        qaPage += "<td></td>"
			#qaPage += '<td> <a href="'+self.webLogCGIBase+'/showStripCharts.py?'
			#qaPage += 'arch='+plat+'&release='+build
			#qaPage += '"> Strip Charts</a> </td>'

                        vgErrs = self.getValgrindErrors(build, plat)
                        if int(vgErrs) > 0:
                            qaPage += ' <td> <a href="'+config.siteInfo['macms01Path']+'/showValgrindResults.py?'
                            qaPage += 'ib='+build+'&arch='+plat
                            qaPage += '"> '+vgErrs+' valgrind errors </a> </td>'
                        else:
                            qaPage += '<td></td>'
                        qaPage = qaSumSubTbl + qaPage 
                        qaPage += '</tr></table>'

                        # ------------------------------------------

                        if 'N/A' in bldInfo:
                            bldTable += '<td> &nbsp; </td> \n'
                        else:
                            bldTable += '<td>' + bldSumm + '&nbsp;' + tstSumm + '&nbsp;' + bldDetails + " " +bldInfo + '</td> \n<td>'+buildLink+'</td>\n'

                        if 'passed; unknown' in rvInfo:
                            rvTable  += '<td> &nbsp; </td> \n'
                        else:
                            rvTable  += '<td>' + rvSumm + '&nbsp;' + rvCmpSumm  + ' &nbsp;' + rvDetails  + " " +rvInfo  + '</td> \n<td>'+pyRelValLogs+'</td>\n'

                        if 'passed; unknown' in aoInfo:
                            aoTable  += '<td> &nbsp; </td> \n'
                        else:
                            aoTable  += '<td>' + aoSumm  + ' &nbsp;' + aoDetails  + " " +aoInfo  + '</td> \n<td> '+addOnLogs+' </td>\n'

                        qaTable  += '<td> ' + qaPage + ' </td>\n'

                        colCount += 1
                        if colCount%1 == 0:
                            bldTable += '</tr>\n<tr>'
                            rvTable  += '</tr>\n<tr>'
                            aoTable  += '</tr>\n<tr>'
                            qaTable  += '</tr>\n<tr>'
                    
                    bldTable += '</tr></table>  <!-- bldTable end -->'
                    rvTable += '</tr></table> <!-- rvTable end -->'
                    aoTable += '</tr></table> <!-- aoTable end -->'
                    qaTable += '</tr></table> <!-- qaTable end -->'
                    
                    platCol += '</table>\n'
                    #if 'N/A' not in bldInfo:
                    self.formatter.writeRow( [day, build, platCol, bldTable, rvTable, aoTable, qaTable], bold, style=rowStyle)
                
            self.formatter.endTable()

            self.formatter.write('<table border="0" cellpadding="3"> <tr>')
            for item in ['passed', 'warning', 'error', 'unknown', 'skipped']:
                itemBox = '<td class="'+item+'"> &nbsp; &nbsp; </td><td>'+item+'</td>'
                self.formatter.write(itemBox)
            self.formatter.write('</tr></table>')
            self.formatter.write("<p>The coloured boxes for the builds refer to | build | tests | information.</p>\n")
            self.formatter.write("<p>The coloured boxes for the Q/A page refer to | valgrind | ignominy | old cfg files | duplicate dictionary | dir/file size | code rules | prod workflow | fwlite | online.</p>\n")
            self.formatter.write("<p></p>\n")

        return


def main():

    style = """
    <link rel="stylesheet" type="text/css" href="%s/intbld.css">

    <style type="text/css">  
    .info { display: none; }
    .mainTable { table-layout:fixed; }
    .showOld { font-size: 18; text-decoration: underline; padding: 20px}
    </style>  

    <script type="text/javascript" src="%s/jsExt/jquery.js"></script>

    <!-- 
    <script type="text/javascript" src="%s/jsExt/dataTables.js"></script>
    -->
    
    <script>
    function showHide(obj){
        var myname = obj.name;
        $(".detail[name='"+myname+"']").toggle();
        $(".info[name='"+myname+"']").toggle();
    }
    
    function toggleIBs(obj) {
        var myname = obj.name;
        if ($(".oldIB[name='"+myname+"']").css('display') == 'none') {
            $(".oldIB[name='"+myname+"']").css('display','block');
            $(".showOld[name='"+myname+"']").html("hide older IBs");
        } else {
            $(".oldIB[name='"+myname+"']").css('display','none');
            $(".showOld[name='"+myname+"']").html("show older IBs");
        }
    }
    </script>

    <script>
    $(document).ready(function() {
       // make the "summary" and "hide summary" underlined
       $(".detail").css('text-decoration', "underline");
       $(".info").css('text-decoration', "underline");
       // $(".oldIB").css('display', "none");
       $(".showOld").css('text-decoration', "underline");
       
       // color rows of tables alternatively for even/odd rows
       //-ap not yet working :(       $(".mainTable tr:even").addClass("alt");

    });
    </script>

    """ % (config.siteInfo['HtmlPath'], config.siteInfo['HtmlPath'], config.siteInfo['HtmlPath'])

    fmtr = Formatter.SimpleHTMLFormatter(title="CMSSW integration builds", style=style)

    bv = BuildViewer(fmtr)
    bv.getListOfBuilds()
    bv.showBuilds()

    return


main()
