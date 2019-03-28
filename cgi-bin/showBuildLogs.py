#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Andreas Pfeiffer on 2009-10-20.
Copyright (c) 2009 CERN. All rights reserved.
"""

# make sure this is first to trap also problems in includes later
import cgitb; cgitb.enable() ## cgitb.enable(display=0, logdir=os.getcwd()+"/../cgi-logs/")

import os, sys, cgi, time, re
from pickle import Unpickler
        
import Formatter

import config

def cleanPath(path):
    return os.path.normpath(os.path.join('/',path))

import getopt

def pkgCmp(a,b):
    if a.subsys == b.subsys: return cmp(a.pkg, b.pkg)
    else: return cmp(a.subsys, b.subsys)

# ================================================================================

class ErrorInfo(object):
    """keeps track of information for errors"""
    def __init__(self, errType, msg):
        super(ErrorInfo, self).__init__()
        self.errType = errType
        self.errMsg  = msg

# ================================================================================

class PackageInfo(object):
    """keeps track of information for each package"""
    def __init__(self, subsys, pkg):
        super(PackageInfo, self).__init__()

        self.subsys  = subsys
        self.pkg     = pkg
        self.errInfo = []
        self.errSummary = {}
        self.errLines = {}
        self.warnOnly = True
        
    def addErrInfo(self, errInfo, lineNo):
        """docstring for addErr"""
        if 'Error' in errInfo.errType: self.warnOnly = False
        self.errInfo.append( errInfo )
        if errInfo.errType not in self.errSummary.keys():
            self.errSummary[errInfo.errType] = 1
        else:
            self.errSummary[errInfo.errType] += 1
        self.errLines[lineNo] = errInfo.errType
        
    def name(self):
        """docstring for name"""
        return self.subsys+'/'+self.pkg
        
# ================================================================================

class BuildLogDisplay(object):

    def __init__(self, fmtr):
        self.formatter = fmtr

        self.styleClass = {'dictError'   : 'dictErr',
                           'compError'   : 'compErr',
                           'linkError'   : 'linkErr',
                           'pythonError' : 'pyErr',
                           'dwnlError'   : 'dwnldErr',
                           'miscError'   : 'miscErr',
                           'compWarning' : 'compWarn',
                           'ignoreWarning' : 'compWarn',
                           'ok'          : 'ok',
                           }

        #self.unitTestLogs = {}
        self.unitTestResults = {}
        self.GPUunitTestResults = {}
        self.IWYU = {}
        self.InvalidIncludes = {}
        self.Python3 = {}
        self.depViolLogs = {}
        self.depViolResults = {}
        self.topCgiLogString = ''
        self.topCgiLogIWYU = ''
        self.topInvalidIncludes = ''
        self.topCgiLogPython3 = ''
        self.addRow = False

        return
      
    # --------------------------------------------------------------------------------

    def getUnitTests(self, path):

        #import glob
        #unitTstLogs = glob.glob(path+'/unitTestLogs/*/*/unitTest.log')
        #for item in unitTstLogs:
        #    words = item.split('/')
        #    pkg = words[-3]+'/'+words[-2]
        #    self.unitTestLogs[pkg] = item
        unitTestResults = {}
        try:
          wwwFile = path+'/unitTestResults.pkl'
          if not os.path.exists(wwwFile): wwwFile=path.replace('www/','')+'/unitTestResults.pkl'
          summFile = open(wwwFile, 'r')
          pklr = Unpickler(summFile)
          unitTestResults = pklr.load()
          summFile.close()
        except IOError, e:
          # print "IO ERROR reading unitTestResuls.pkl file from ", path, str(e)
          pass
        except Exception, e:
          print "ERROR got exception when trying to load unitTestResults.pkl", str(e)

        return unitTestResults
      
    # --------------------------------------------------------------------------------

    def getPython3(self, path):
        self.Python3={}
        try:
          py3 = os.path.join(path, "python3.log")
          if os.path.exists (py3):
            log = open(py3, 'r')
            for line in [l for l in log.readlines() if ' Error compiling ' in l]:
              pkg_parts = []
              if   "'cfipython/" in line: pkg_parts=line.split("'cfipython/",2)[-1].split("/",2)[:2]
              elif "'python/"    in line: pkg_parts=line.split("'python/",1)[-1].split("/",2)[:2]
              elif "'src/"       in line: pkg_parts=line.split("'src/",1)[-1].split("/",2)[:2]
              if pkg_parts: self.Python3["/".join(pkg_parts)]=1
        except Exception, e:
          print "ERROR got exception when trying to read python3.log", str(e)
        return

    # --------------------------------------------------------------------------------

    def getIWYU(self, rel, arch, jenkins_dir):
        self.IWYU={}
        try:
          stats = os.path.join(jenkins_dir, "iwyu", rel, arch, "stats.json")
          if os.path.exists (stats):
            from json import load
            with open(stats) as sfile:    
              self.IWYU = load(sfile)
        except Exception, e:
          print "ERROR got exception when trying to load stats.json", str(e)
        return

    # --------------------------------------------------------------------------------

    def getInvalidIncludes(self, rel, arch, jenkins_dir):
        self.InvalidIncludes = {}
        try:
          stats = os.path.join(jenkins_dir, "invalid_includes", rel, arch, "summary.json")
          if os.path.exists (stats):
            from json import load
            with open(stats) as sfile:
              self.InvalidIncludes = load(sfile)
        except Exception, e:
          print "ERROR got exception when trying to load summary.json", str(e)
        return
    # --------------------------------------------------------------------------------

    def showUnitTest(self, pkg, row, rowStyle, unitTestResults, utype="") :

        pkgOK = True
        if not unitTestResults: return pkgOK
        col = ' - '
        colStyle = ' '

        # add the unit-test log file if available
        #if pkg.name() in self.unitTestLogs.keys():        
        #    unitTestLog = 'unknown'
        #    colStyle = ' '
        #    nFail       = 0
        if pkg.name() in unitTestResults.keys():
                self.addRow = True
                nOK = unitTestResults[pkg.name()][-2]
                nFail = unitTestResults[pkg.name()][-1]
                colStyle = 'ok'
                if nFail > 0 :
                    colStyle = 'failed'
                    pkgOK = False
                    
                unitTestLog = ' OK:'+str(nOK)
                unitTestLog += '/ Fail: '+str(nFail)
                if unitTestLog != 'unknown':
                    unitTestLog = ' <a href="'+self.topCgiLogString+utype+'unitTestLogs/'+pkg.name()+'"> '+unitTestLog+' </a>'
                    col = unitTestLog.replace(self.normPath, self.unitTestLogBase) 
                else:
                    col = ' - '
                    colStyle = ' '
                    
        row.append( col )
        rowStyle.append( colStyle )
    
        return pkgOK
    
    # --------------------------------------------------------------------------------

    def getDepViol(self, path):
    
        try:
            wwwFile = path+'/testLogs/depViolationSummary.pkl'
            if not os.path.exists(wwwFile): path.replace('www/','')+'/testLogs/depViolationSummary.pkl'
            summFile = open(wwwFile, 'r')
            pklr = Unpickler(summFile)
            results = pklr.load()
            summFile.close()
        except IOError, e:
            # print "IO ERROR reading depViolationSummary.pkl file from ", path, str(e)
            self.depViolResults = {}
            return
        except Exception, e:
            print "ERROR got exception when trying to load depViolationSummary.pkl", str(e)

        for k,v in results.items():
            pkg = '/'.join( k.split('/')[0:2] )
            prod = k.split('/')[-1]
            self.depViolResults[pkg] = [v,prod]

        # now get the log files (from two levels below the package: <product> or (test/plugins/)<product> )
        import glob
        wwwFile = path+'/etc/dependencies/depViolationLogs'
        if not os.path.exists(wwwFile): wwwFile=path.replace('www/','')+'/etc/dependencies/depViolationLogs'

        depViolLogs = glob.glob(wwwFile+'/*/*/log.txt')
        if depViolLogs:
            for item in depViolLogs:
                self.depViolLogs[ "/".join(item.split("/")[-3:-1])] = item.replace(wwwFile+"/","").replace("/log.txt","")
            return
        return
  
    # --------------------------------------------------------------------------------

    def showDepViol(self, pkg, row, rowStyle) :

        pkgOK =  True
        if not self.depViolResults : return pkgOK

        col = ' - '
        colStyle = ' '
        if pkg.name() in self.depViolResults.keys():
            nFail = self.depViolResults[pkg.name()][0]
            depViolLog = str(nFail) + ' violation'
            if nFail > 1 : depViolLog += 's'
            if pkg.name() in self.depViolLogs:
              col = ' <a href="'+self.topCgiLogString+"depViolationLogs/"+self.depViolLogs[pkg.name()]+'"> '+depViolLog+' </a>'
            else:
              col = "X"
            colStyle = 'failed'
            pkgOK = False
            self.addRow = True
            
        row.append( col )
        rowStyle.append( colStyle )

        return pkgOK
    
    # --------------------------------------------------------------------------------

    def showIWYU(self, pkg, row, rowStyle) :
        pname = pkg.name()
        pkgOK =  True
        if not self.IWYU : return pkgOK
        col = ' - '
        colStyle = ' '
        if pkg.name() in self.IWYU:
            nFail = self.IWYU[pname][0]
            iwyuLog = str(nFail)
            col = ' <a href="'+self.topCgiLogIWYU+pname+'/index.html"> '+iwyuLog+' </a>'
            colStyle = 'failed'
            pkgOK = False
            self.addRow = True
        row.append( col )
        rowStyle.append( colStyle )
        return pkgOK

    # --------------------------------------------------------------------------------

    def showInvalidIncludes(self, pkg, row, rowStyle) :
        pname = pkg.name()
        pkgOK =  True
        if not self.InvalidIncludes : return pkgOK
        col = ' - '
        colStyle = ' '
        if pkg.name() in self.InvalidIncludes:
            col = ' <a href="'+self.topInvalidIncludes+pname+'"> '+str(self.InvalidIncludes[pname])+' </a>'
            colStyle = 'failed'
            pkgOK = False
            self.addRow = True
        row.append( col )
        rowStyle.append( colStyle )
        return pkgOK
    
    # --------------------------------------------------------------------------------

    def showPython3(self, pkg, row, rowStyle) :
        pname = pkg.name()
        pkgOK =  True
        if not self.Python3 : return pkgOK
        col = ' - '
        colStyle = ' '
        if pkg.name() in self.Python3:
            col = ' <a href="'+self.topCgiLogPython3+'"> 1 </a>'
            colStyle = 'failed'
            pkgOK = False
            self.addRow = True
        row.append( col )
        rowStyle.append( colStyle )
        return pkgOK

    # --------------------------------------------------------------------------------

    def showLibChecks(self, pkg, row, rowStyle) :

        pkgOK = True
        if not self.libChkErrMap : return pkgOK # no info available, claim it's OK
        
        col = ' - '
        colStyle = ' '
        if self.libChkErrMap.has_key(pkg.name()) and len(self.libChkErrMap[pkg.name()])>0:
            detailId = 'lc_'+pkg.name().replace('/','_')
            info =  "hide<br/> unnecessary direct dependencies: <br/> "
            info += '<br/>'.join(self.libChkErrMap[pkg.name()]).replace('Unnecessary direct dependence','')
            summ = str( len( self.libChkErrMap[pkg.name()] ) )
            bldDetails = '<a class="detail" name="'+detailId+'" onclick="showHide(this) "> &nbsp;'+summ+'&nbsp; </a>'
            bldInfo    = '<a class="info"   name="'+detailId+'" onclick="showHide(this) "> '+info+' </a>'
            col =  bldDetails + bldInfo 
            pkgOK = False
            self.addRow = True

        row.append( col )
        rowStyle.append( colStyle )

        return pkgOK
    
    # --------------------------------------------------------------------------------

    def showScramErrors(self, pkg, row, rowStyle):

        pkgOK = True
        if not self.sa.errPkg : return pkgOK
        
        col = ' - '
        colStyle = ' '
        if len(self.sa.errPkg.keys()) > 0:
            if self.sa.errPkg.has_key(pkg.name()):
                pkgOK = False
                self.addRow = True
                detailId = 'scerr1_'+pkg.name().replace('/','_')
                info = "hide<br/> <br/> " + '<br/>'.join(self.sa.errPkg[pkg.name()])
                summ = str( len( self.sa.errPkg[pkg.name()] ) )
                bldDetails = '<a class="detail" name="'+detailId+'" onclick="showHide(this) "> &nbsp;'+summ+'&nbsp; </a>'
                bldInfo    = '<a class="info"   name="'+detailId+'" onclick="showHide(this) "> '+info+' </a>'
                col = bldDetails + bldInfo
                self.addRow = True

        row.append( col )
        rowStyle.append( colStyle )

        return pkgOK
    
    # --------------------------------------------------------------------------------

    def showScramWarnings(self, pkg, row, rowStyle):

        pkgOK = True
        if not self.sa.warnPkg : return pkgOK
        
        col = ' - '
        colStyle = ' '
        if len(self.sa.warnPkg.keys()) > 0:
            if self.sa.warnPkg.has_key(pkg.name()):
                pkgOK = False
                detailId = 'scwarn1_'+pkg.name().replace('/','_')
                info = "hide<br/> <br/> " + '<br/>'.join(self.sa.warnPkg[pkg.name()])
                summ = str( len( self.sa.warnPkg[pkg.name()] ) )
                bldDetails = '<a class="detail" name="'+detailId+'" onclick="showHide(this) "> &nbsp;'+summ+'&nbsp; </a>'
                bldInfo    = '<a class="info"   name="'+detailId+'" onclick="showHide(this) "> '+info+' </a>'
                col = bldDetails + bldInfo
                self.addRow = True

        row.append( col )
        rowStyle.append( colStyle )

        return pkgOK

    # --------------------------------------------------------------------------------

    def showLogInfo(self):
        
        pathReq = ""
        testName = None
        try:
            scriptName = os.environ["SCRIPT_NAME"]
            requestURI = os.environ["REQUEST_URI"].split('?',1)[0]
            if '?' in os.environ["REQUEST_URI"]: testName = os.environ["REQUEST_URI"].split('?',1)[-1]
            pathReq = cleanPath( requestURI.replace(scriptName,'') )
        except:
            pathReq = sys.argv[1]
            pass

        fwlite = False
        if pathReq.startswith("/fwlite/"):
          pathReq = pathReq.replace("/fwlite/", "/")
          fwlite = True
        jenkinsLogs = '/data/sdt/SDT/jenkins-artifacts'
        topLogDir = '/data/sdt/buildlogs/'
        fullPath = topLogDir + pathReq
        self.normPath = os.path.normpath( fullPath )

        logBaseURL = config.siteInfo['HtmlPath']+'/rc/'
        newdir = "new"
        if fwlite: newdir = "new_FWLITE"
        topLogString = logBaseURL + pathReq+'/'+newdir+'/'
        self.unitTestLogBase = logBaseURL + pathReq
        self.depViolLogBase = logBaseURL + pathReq

        ib = self.normPath.split('/')[-1]

        self.formatter.writeAnchor(ref='top')

        # read back all info also as pkl files so we can re-use it:

        try:
            summFile = open(self.normPath+'/'+newdir+'/logAnalysis.pkl','r')
        except:
            self.formatter.writeH3("ERROR could not open results from logAnalysis")
            # if this happens, don't bother to continue
            return

        pklr = Unpickler(summFile)
        [rel, plat, anaTime]   = pklr.load()
        errorKeys   = pklr.load()
        nErrorInfo  = pklr.load()
        errMapAll   = pklr.load()
        packageList = pklr.load()
        topURL      = pklr.load()
        errMap      = pklr.load()
        tagList     = pklr.load()
        pkgOK       = pklr.load()
        summFile.close()
        origPkgList = {}
        rel = rel.replace("_FWLITE","")
        for p in packageList: origPkgList[p.name()] = 1

        self.topCgiLogString = config.siteInfo['CgiHtmlPath']+'logreader/'+plat+'/'+ib+'/'
        self.topCgiLogIWYU   = config.siteInfo['CgiHtmlPath']+'buildlogs/iwyu/'+plat+'/'+ib+'/'
        self.topInvalidIncludes = '/SDT/jenkins-artifacts/invalid_includes/'+plat+'/'+ib+'/'
        self.topCgiLogPython3   = config.siteInfo['CgiHtmlPath']+'buildlogs/python3/'+plat+'/'+ib+'/python3.log'
        if fwlite: self.topCgiLogString = config.siteInfo['CgiHtmlPath']+'buildlogs/fwlite/'+plat+'/'+ib+'/'
        # read libChecker info
        self.libChkErrMap = {}
        if not fwlite and ((not testName) or (testName=='libchk')):
          try:
            libChkFile = open(self.normPath+'/new/libchk.pkl','r')
            lcPklr = Unpickler(libChkFile)
            self.libChkErrMap = lcPklr.load()
            libChkFile.close()
          except IOError:
            # self.formatter.write("ERROR : could not find/read libchecker info")
            self.libChkErrMap = {}
          except Exception, e:
            self.formatter.write("ERROR : unknown error reading libchecker info : "+str(e))
            self.libChkErrMap = {}
            
        # get scram info
        try:
            logFile = open(self.normPath+'/scramInfo.log', 'r')
            linesScram = logFile.readlines()
            logFile.close()
        except:
            linesScram = []

        from showScramInfo import ScramAnalyzer
        self.sa = ScramAnalyzer(self.formatter)
        self.sa.analyzeLogFile(linesScram)
        
        if rel != ib:
            print "Error : found ", rel, 'when expecting ', ib

        keyList = errorKeys
        #Make sure we have styleClass for keys if not then set then to error
        for key in keyList:
            try:
                val = self.styleClass[key]
            except KeyError:
               self.styleClass[key] = 'compErr'

        backToPortal = ' -- <a href="'+config.siteInfo['CgiHtmlPath']+'showIB.py">Back to IB portal</a>'
        self.formatter.writeH3('Summary for ' + ib + ' IB on platform ' + plat + backToPortal)

        totErr = 0
        for key, val in nErrorInfo.items():
            totErr += int(val)
        totErr += len(self.libChkErrMap.keys())
        
        if not fwlite:
          if (not testName) or (testName=='utests'):
            self.unitTestResults = self.getUnitTests(self.normPath)
          if (not testName) or (testName=='gpu_utests'):
            self.GPUunitTestResults = self.getUnitTests(self.normPath+"/GPU")
          if (not testName) or (testName=='DepViol'):
            self.getDepViol(self.normPath)
          if (not testName) or (testName=='IWYU'):
            self.getIWYU(ib, plat, jenkinsLogs)
          if (not testName) or (testName=='InvalidIncludes'):
            self.getInvalidIncludes(ib, plat, jenkinsLogs)
          if (not testName) or (testName=='python3'):
            self.getPython3(self.normPath)

        lcErrs = 0
        if not fwlite: 
          for pkg in self.libChkErrMap.keys() :
            if len(self.libChkErrMap[pkg])>0: lcErrs += 1

        # summary table
        self.formatter.startTable([30,10,10],['error type','# of packages', 'total # of errors'])
        emptyKeys = []
        for key in keyList:
            val = 0
            try:
                val = nErrorInfo[key]
            except KeyError:
                pass
            nPkgE = len(errMapAll[key])
            if nPkgE == 0: emptyKeys.append(key)
            self.formatter.writeStyledRow([key, str(nPkgE), str(val)], [self.styleClass[key],self.styleClass[key],self.styleClass[key]])
            
        if (not fwlite) and self.depViolResults: 
            self.formatter.writeStyledRow(['dependency violations', str(len(self.depViolResults.keys()))  , ' unknown '], ['scErr', 'scErr', 'scErr'] )
        scErrLink = '<a href="'+logBaseURL+pathReq+'/scramInfo.log">scram errors</a>'
        self.formatter.writeStyledRow([scErrLink , str(len(self.sa.errPkg.keys())+self.sa.errEx)   , ' unknown '], ['scErr', 'scErr', 'scErr'] )
        scWarnLink = '<a href="'+logBaseURL+pathReq+'/scramInfo.log">scram warnings</a>'
        self.formatter.writeStyledRow([scWarnLink, str(len(self.sa.warnPkg.keys())+self.sa.warnEx)  , ' unknown '], ['scWarn', 'scWarn', 'scWarn'] )
        if not fwlite: self.formatter.writeStyledRow(['libChecker'    , str(lcErrs), ' unknown '], ['lcErr', 'lcErr', 'lcErr'] )
        self.formatter.endTable()

        # --------------------------------------------------------------------------------
        self.formatter.writeH3("Log file from the BuildManager")
        self.formatter.write("<ul>")
        self.formatter.write('<li><a href="'+topLogString+'../../fullLog">Log file from the BuildManager (check here if something _completly_ fails).</a></li>')
        self.formatter.write('<li><a href="'+topLogString+'../prebuild.log">Log file from "scram p" and CVS checkout.  </a></li>')
        self.formatter.write('<li><a href="'+topLogString+'../release-build.log">Log file from "scram b".  </a></li>')
        self.formatter.write("</ul>")

        msg = '<br />'
        msg += 'For the new libchecker errors and the SCRAM errors and warnings please click '
        msg += 'on the linked number to see the details for the package.'
        msg += ''
        self.formatter.writeH3(msg)

        ignoreKeys = ['dwnlError','ignoreWarning']
        hdrs = ['#/status','subsystem/package']
        szHdr = [3,20]
        for key in keyList:
            if key in ignoreKeys: continue
            if key in emptyKeys: continue
            hdrs.append(key)
            szHdr.append(10)

        #  add headers for scram
        if len(self.sa.errPkg.keys()) > 0:
            hdrs.append('SCRAM errors')
            szHdr.append(20)
        if len(self.sa.warnPkg.keys()) > 0:
            hdrs.append('SCRAM warnings')
            szHdr.append(20)

        # and a column for the dependency violations:
        if not fwlite and self.depViolResults :
            hdrs.append('Dependency <br/> violations')
            szHdr.append(20)
        
        # and a column for the unitTests:
        if not fwlite and self.unitTestResults:
          hdrs.append('UnitTest')
          szHdr.append(20)

        # and a column for the GPU unitTests:
        if not fwlite and self.GPUunitTestResults:
          hdrs.append('GPU UnitTest')
          szHdr.append(20)
        
        #  add headers for libcheck
        if (not fwlite) and len( self.libChkErrMap.keys() ) > 0:
            hdrs.append('libCheck')
            szHdr.append(20)            

        #  add headers for IWYU
        if (not fwlite) and len(self.IWYU.keys()) > 0:
            hdrs.append('IWYU')
            szHdr.append(20)

        #  add headers for InvalidIncludes
        if (not fwlite) and len(self.InvalidIncludes.keys()) > 0:
            hdrs.append('InvalidIncludes')
            szHdr.append(20)

        #  add headers for Python3
        if (not fwlite) and len(self.Python3.keys()) > 0:
            hdrs.append('Python3')
            szHdr.append(20)

        self.formatter.startTable(szHdr, hdrs)
        rowIndex = 0
        # --------------------------------------------------------------------------------
        # first check the build errors, these have highest priority:
        allErrPkgs = {}
        for key in keyList:
            pkgList = errMap[key]
            if len(pkgList)==0: continue
            if (key in ignoreKeys) or (key in emptyKeys): 
                for pkg in pkgList: pkgOK.append(pkg)
                continue
            pkgList.sort(pkgCmp)
            
            for pkg in pkgList:
                allErrPkgs[pkg.name()]=1
                styleClass = 'ok'
                for cKey in errorKeys :
                    if styleClass == 'ok'  and cKey in pkg.errSummary.keys(): styleClass = self.styleClass[cKey]
                link = pkg.name()
                if link in origPkgList: link = ' <a href="'+self.topCgiLogString+pkg.name()+'">'+pkg.name()+'   '+tagList[pkg.name()]+'  </a> '
                row = ['&nbsp;'+str(rowIndex), link]
                rowStyle = [styleClass, ' ']

                for pKey in keyList:
                    if (pKey in ignoreKeys) or (pKey in emptyKeys): continue
                    if pKey in pkg.errSummary.keys():
                        row.append( str(pkg.errSummary[pKey]) )
                        rowStyle.append( ' ' )
                    else:
                        row.append( ' - ' )
                        rowStyle.append( ' ' )
                self.addRow = False
                # SCRAM errors
                self.showScramErrors(pkg, row, rowStyle)
            
                # SCRAM warnings
                self.showScramWarnings(pkg, row, rowStyle)

                if not fwlite:
                  # add the dependency violation log file if available
                  self.showDepViol(pkg, row, rowStyle)
                  # add the unit-test log file if available
                  self.showUnitTest(pkg, row, rowStyle, self.unitTestResults)
                  # add the GPU unit-test log file if available
                  self.showUnitTest(pkg, row, rowStyle, self.GPUunitTestResults, "GPU")
                  # libchecker
                  self.showLibChecks(pkg, row, rowStyle)
                  # IWYU
                  self.showIWYU(pkg, row, rowStyle)
                  # InvalidIncludes
                  self.showInvalidIncludes(pkg, row, rowStyle)
                  # Python3
                  self.showPython3(pkg, row, rowStyle)

                if not testName: self.addRow=True
                if not self.addRow: continue
                rowIndex += 1
                self.formatter.writeStyledRow(row,rowStyle)

        # --------------------------------------------------------------------------------
        # check for other errors (depviol, scram warnings/errors, libchecker) in remaining "OK" packages
        for p in tagList:
          if p in allErrPkgs: continue
          found = False
          for pk in pkgOK:
            if pk.name() == p:
              found=True
              break
          if not found:
            s = p.split("/",1)
            x= PackageInfo(s[0],s[1])
            pkgOK.append(x)
        pkgList = pkgOK
        pkgList.sort(pkgCmp)
        newOK = []
        libChkOnly = []
        for pkg in pkgList:
            # set defaults for the first columns, these are OK
            self.addRow = False
            link = pkg.name()
            if link in origPkgList: link = ' <a href="'+self.topCgiLogString+pkg.name()+'">'+pkg.name()+'   '+tagList[pkg.name()]+'</a> '
            row = ['&nbsp;'+str(rowIndex), link]
            rowStyle = ['lcErr', ' ']
            for pKey in errorKeys:
                if (pKey in ignoreKeys) or (pKey in emptyKeys): continue
                row.append( ' - ' )
                rowStyle.append( ' ' )

            # SCRAM errors
            isOK = self.showScramErrors(pkg, row, rowStyle)
            
            # SCRAM warnings
            isOK = self.showScramWarnings(pkg, row, rowStyle) and isOK
             
            # add the dependency violation log file if available
            isOK1 = True
            if not fwlite: 
              #dependency violations
              isOK = self.showDepViol(pkg, row, rowStyle)  and isOK
              # add the unit-test log file if available
              isOK = self.showUnitTest(pkg, row, rowStyle, self.unitTestResults) and isOK
              # add the unit-test log file if available
              isOK = self.showUnitTest(pkg, row, rowStyle, self.GPUunitTestResults, "GPU") and isOK
              # libChecker
              isOK1 = self.showLibChecks(pkg, row, rowStyle)
              # IWYU
              isOK = self.showIWYU(pkg, row, rowStyle) and isOK
              # InvalidIncludes
              isOK = self.showInvalidIncludes(pkg, row, rowStyle) and isOK
              # Python3
              isOK = self.showPython3(pkg, row, rowStyle) and isOK

            if not testName: self.addRow=True
            if isOK1 and isOK:
                newOK.append(pkg) 
            elif not isOK1 and isOK:
                libChkOnly.append(pkg)
            elif self.addRow:
                rowIndex += 1
                self.formatter.writeStyledRow(row,rowStyle)

        # --------------------------------------------------------------------------------

        # here we have the packages which have _only_ a libcheck error
        pkgList = libChkOnly
        pkgList.sort(pkgCmp)
        for pkg in pkgList:
            self.addRow = False
            link = pkg.name()
            if link in origPkgList: link = ' <a href="'+self.topCgiLogString+pkg.name()+'">'+pkg.name()+'   '+tagList[pkg.name()]+'</a> '
            row = ['&nbsp;'+str(rowIndex), link]
            rowStyle = ['lcerr', ' ']

            for pKey in errorKeys:
                if pKey in ignoreKeys: continue
                if pKey in emptyKeys: continue

                row.append( ' - ' )
                rowStyle.append( ' ' )

            # add empty cols for the other errors
            if len(self.sa.errPkg.keys()) > 0:
                row.append( ' - ' )
                rowStyle.append( ' ' )
                
            if len(self.sa.warnPkg.keys()) > 0:
                row.append( ' - ' )
                rowStyle.append( ' ' )

            if not fwlite: 
              # add the dependency violation log file if available
              self.showDepViol(pkg, row, rowStyle)
              # add the unit-test log file if available
              self.showUnitTest(pkg, row, rowStyle, self.unitTestResults)
              # add the unit-test log file if available
              self.showUnitTest(pkg, row, rowStyle, self.GPUunitTestResults, "GPU")
              # if len( self.libChkErrMap.keys() ) > 0:
              self.showLibChecks(pkg, row, rowStyle)
              # if len( self.IWYU.keys() ) > 0:
              self.showIWYU(pkg, row, rowStyle)
              # if len( self.InvalidIncludes.keys() ) > 0:
              self.showInvalidIncludes(pkg, row, rowStyle)
              # Python3
              self.showPython3(pkg, row, rowStyle)

            if not testName: self.addRow=True
            if not self.addRow: continue
            rowIndex += 1
            self.formatter.writeStyledRow(row,rowStyle)

        # --------------------------------------------------------------------------------

        # here we have the really OK packages
        pkgList = newOK
        pkgList.sort(pkgCmp)
        for pkg in pkgList:
            self.addRow = False
            # skip these, they were treated above ...
            if pkg.name() in self.libChkErrMap.keys() and len(self.libChkErrMap[pkg.name()])>0: continue
            link = pkg.name()
            if link in origPkgList: link = ' <a href="'+self.topCgiLogString+pkg.name()+'">'+pkg.name()+'   '+tagList[pkg.name()]+'</a> '
            row = ['&nbsp;'+str(rowIndex), link]
            rowStyle = ['ok', ' ']

            for pKey in errorKeys:
                if pKey in ignoreKeys: continue
                if pKey in emptyKeys: continue

                row.append( ' - ' )
                rowStyle.append( ' ' )

            # add empty cols for the other errors
            if len(self.sa.errPkg.keys()) > 0:
                row.append( ' - ' )
                rowStyle.append( ' ' )
                
            if len(self.sa.warnPkg.keys()) > 0:
                row.append( ' - ' )
                rowStyle.append( ' ' )

            # add the dependency violation log file if available
            if not fwlite: self.showDepViol(pkg, row, rowStyle)
            
            # add the unit-test log file if available
            if not fwlite:
              self.showUnitTest(pkg, row, rowStyle, self.unitTestResults)
              self.showUnitTest(pkg, row, rowStyle, self.GPUunitTestResults, "GPU")
                    
            if (not fwlite) and len( self.libChkErrMap.keys() ) > 0:
                row.append( ' - ' )
                rowStyle.append( ' ' )
            if not testName: self.addRow=True
            if not self.addRow: continue
            rowIndex += 1
            self.formatter.writeStyledRow(row,rowStyle)

        # --------------------------------------------------------------------------------

        self.formatter.endTable()

        return


def main():

    style = """
    
    <!-- bootstrap style -->
    <link rel="stylesheet" type="text/css" href="%s/css/libs/bootstrap.min.css">
    <link rel="stylesheet" type="text/css" href="%s/css/intbld.css">
    <style type="text/css">  
    // @import url(css.css);  
    </style>  
    <style type="text/css">  
    .info { display: none; }
    </style>  
    
    <!-- jQuery library -->
    <script type="text/javascript" src="%s/js/libs/jquery.min.js"></script>
    <!-- bootstrap library -->
    <script type="text/javascript" src="%s/js/libs/bootstrap.min.js"></script>
    
    <script>
    function showHide(obj){
        myname = obj.name;
        $(".detail[name='"+myname+"']").toggle();
        $(".info[name='"+myname+"']").toggle();
    }
    </script>

    <script>
    $(document).ready(function()
    {
    // $("table ").css('text-align', "center");
    // make the "summary" and "hide summary" underlined
    //(".detail").css('text-decoration', "underline");
    // $(".info").css('text-decoration', "underline");
    // color rows of tables alternatively for even/odd rows
    // $("tr:even").css("background-color", 'rgb(234, 235, 255)');
    // $("tr:odd").css("background-color",  'rgb(211, 214, 255)');
    });
    </script>

    """ % (config.siteInfo['HtmlPath'], config.siteInfo['HtmlPath'], config.siteInfo['HtmlPath'], config.siteInfo['HtmlPath'])

    fmtr = Formatter.SimpleHTMLFormatter(title="CMSSW Integration Build Info", style=style)

    bld = BuildLogDisplay(fmtr)
    bld.showLogInfo()

if __name__ == '__main__' :
    main()
    
