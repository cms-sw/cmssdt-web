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
        self.IWYU = {}
        self.depViolLogs = {}
        self.depViolResults = {}
        self.topCgiLogString = ''
        self.topCgiLogIWYU = ''

        return
      
    # --------------------------------------------------------------------------------

    def getUnitTests(self, path):

        #import glob
        #unitTstLogs = glob.glob(path+'/unitTestLogs/*/*/unitTest.log')
        #for item in unitTstLogs:
        #    words = item.split('/')
        #    pkg = words[-3]+'/'+words[-2]
        #    self.unitTestLogs[pkg] = item

        try:
          wwwFile = path+'/unitTestResults.pkl'
          if not os.path.exists(wwwFile): wwwFile=path.replace('www/','')+'/unitTestResults.pkl'
          summFile = open(wwwFile, 'r')
          pklr = Unpickler(summFile)
          self.unitTestResults = pklr.load()
          summFile.close()
        except IOError, e:
          # print "IO ERROR reading unitTestResuls.pkl file from ", path, str(e)
          self.unitTestResults = {}
          pass
        except Exception, e:
          print "ERROR got exception when trying to load unitTestResults.pkl", str(e)

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

    def showUnitTest(self, pkg, row, rowStyle) :

        pkgOK = True
        col = ' - '
        colStyle = ' '

        # add the unit-test log file if available
        #if pkg.name() in self.unitTestLogs.keys():        
        #    unitTestLog = 'unknown'
        #    colStyle = ' '
        #    nFail       = 0
        if pkg.name() in self.unitTestResults.keys():
                nOK = self.unitTestResults[pkg.name()][-2]
                nFail = self.unitTestResults[pkg.name()][-1]
                colStyle = 'ok'
                if nFail > 0 :
                    colStyle = 'failed'
                    pkgOK = False
                    
                unitTestLog = ' OK:'+str(nOK)
                unitTestLog += '/ Fail: '+str(nFail)
                if unitTestLog != 'unknown':
                    unitTestLog = ' <a href="'+self.topCgiLogString+'unitTestLogs/'+pkg.name()+'"> '+unitTestLog+' </a>'
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
            # self.unitTestResults = {}
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
                detailId = 'scerr1_'+pkg.name().replace('/','_')
                info = "hide<br/> <br/> " + '<br/>'.join(self.sa.errPkg[pkg.name()])
                summ = str( len( self.sa.errPkg[pkg.name()] ) )
                bldDetails = '<a class="detail" name="'+detailId+'" onclick="showHide(this) "> &nbsp;'+summ+'&nbsp; </a>'
                bldInfo    = '<a class="info"   name="'+detailId+'" onclick="showHide(this) "> '+info+' </a>'
                col = bldDetails + bldInfo 

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

        row.append( col )
        rowStyle.append( colStyle )

        return pkgOK

    # --------------------------------------------------------------------------------

    def showLogInfo(self):
        
        pathReq = ""
        try:
            scriptName = os.environ["SCRIPT_NAME"]
            requestURI = os.environ["REQUEST_URI"]
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

        self.topCgiLogString = config.siteInfo['CgiHtmlPath']+'buildlogs/'+plat+'/'+ib+'/'
        self.topCgiLogIWYU   = config.siteInfo['CgiHtmlPath']+'buildlogs/iwyu/'+plat+'/'+ib+'/'
        if fwlite: self.topCgiLogString = config.siteInfo['CgiHtmlPath']+'buildlogs/fwlite/'+plat+'/'+ib+'/'
        # read libChecker info
        self.libChkErrMap = {}
        if not fwlite:
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
          self.getUnitTests(self.normPath)
          self.getDepViol(self.normPath)
          self.getIWYU(ib, plat, jenkinsLogs)

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
        if not fwlite:
          hdrs.append('UnitTest logfile')
          szHdr.append(20)
        
        #  add headers for libcheck
        if (not fwlite) and len( self.libChkErrMap.keys() ) > 0:
            hdrs.append('libCheck')
            szHdr.append(20)            

        #  add headers for IWYU
        if (not fwlite) and len(self.IWYU.keys()) > 0:
            hdrs.append('IWYU')
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

                # SCRAM errors
                self.showScramErrors(pkg, row, rowStyle)
            
                # SCRAM warnings
                self.showScramWarnings(pkg, row, rowStyle)

                if not fwlite:
                  # add the dependency violation log file if available
                  self.showDepViol(pkg, row, rowStyle)
                  # add the unit-test log file if available
                  self.showUnitTest(pkg, row, rowStyle)
                  # libchecker
                  self.showLibChecks(pkg, row, rowStyle)
                  # IWYU
                  self.showIWYU(pkg, row, rowStyle)

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
            isOK = True

            # set defaults for the first columns, these are OK
            link = pkg.name()
            if link in origPkgList: link = ' <a href="'+self.topCgiLogString+pkg.name()+'">'+pkg.name()+'   '+tagList[pkg.name()]+'</a> '
            row = ['&nbsp;'+str(rowIndex), link]
            rowStyle = ['lcErr', ' ']
            for pKey in errorKeys:
                if (pKey in ignoreKeys) or (pKey in emptyKeys): continue
                row.append( ' - ' )
                rowStyle.append( ' ' )

            # have to get each status and then check them all. A simpler :
            # isOK = isOK and self.show...
            # will not execute the self.show... method if isOK is already False ...
            
            # SCRAM errors
            isOK2 = self.showScramErrors(pkg, row, rowStyle)
            
            # SCRAM warnings
            isOK3 = self.showScramWarnings(pkg, row, rowStyle)
             
            # add the dependency violation log file if available
            isOK4 = True
            isOK5 = True
            isOK1 = True
            isOK6 = True
            if not fwlite: 
              #dependency violations
              isOK4 = self.showDepViol(pkg, row, rowStyle)
              # add the unit-test log file if available
              isOK5 = self.showUnitTest(pkg, row, rowStyle)
              # libChecker
              isOK1 = self.showLibChecks(pkg, row, rowStyle)
              # libChecker
              isOK6 = self.showIWYU(pkg, row, rowStyle)
                
            if isOK1 and isOK2 and isOK3 and isOK4 and isOK5 and isOK6:
                # store for last part
                newOK.append(pkg) 
            elif not isOK1 and isOK2 and isOK3 and isOK4 and isOK5 and isOK6:
                libChkOnly.append(pkg)
            else:
                rowIndex += 1
                self.formatter.writeStyledRow(row,rowStyle)

        # --------------------------------------------------------------------------------

        # here we have the packages which have _only_ a libcheck error
        pkgList = libChkOnly
        pkgList.sort(pkgCmp)
        for pkg in pkgList:
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
              self.showUnitTest(pkg, row, rowStyle)
              # if len( self.libChkErrMap.keys() ) > 0:
              self.showLibChecks(pkg, row, rowStyle)
              # if len( self.IWYU.keys() ) > 0:
              self.showIWYU(pkg, row, rowStyle)
                
            rowIndex += 1
            self.formatter.writeStyledRow(row,rowStyle)

        # --------------------------------------------------------------------------------

        # here we have the really OK packages
        pkgList = newOK
        pkgList.sort(pkgCmp)
        for pkg in pkgList:
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
            if not fwlite: self.showUnitTest(pkg, row, rowStyle)
                    
            if (not fwlite) and len( self.libChkErrMap.keys() ) > 0:
                row.append( ' - ' )
                rowStyle.append( ' ' )

            rowIndex += 1
            self.formatter.writeStyledRow(row,rowStyle)

        # --------------------------------------------------------------------------------

        self.formatter.endTable()

        return


def main():

    style = """
    <link rel="stylesheet" type="text/css" href="%s/intbld.css">

    <style type="text/css">  
    @import url(css.css);  
    </style>  

    <style type="text/css">  
    .info { display: none; }
    </style>  

    <script type="text/javascript" src="%s/jsExt/jquery.js"></script>

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
    $("table ").css('text-align', "center");
    // make the "summary" and "hide summary" underlined
    $(".detail").css('text-decoration', "underline");
    $(".info").css('text-decoration', "underline");
    // color rows of tables alternatively for even/odd rows
    $("tr:even").css("background-color", 'rgb(234, 235, 255)');
    $("tr:odd").css("background-color",  'rgb(211, 214, 255)');
    });
    </script>

    """ % (config.siteInfo['HtmlPath'], config.siteInfo['HtmlPath'])

    fmtr = Formatter.SimpleHTMLFormatter(title="CMSSW Integration Build Info", style=style)

    bld = BuildLogDisplay(fmtr)
    bld.showLogInfo()

if __name__ == '__main__' :
    main()
    
