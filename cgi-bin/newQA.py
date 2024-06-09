#!/usr/bin/env python3

import os, sys, time, re, urllib, cgi, glob
from subprocess import getstatusoutput
import cgitb; cgitb.enable() ## cgitb.enable(display=0, logdir=os.getcwd()+"/../cgi-logs/")

scriptPath = '/var/www/cgi-bin/'
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

# make sure we have the config info for the web pages
import config

# get the helpers to check the inputs from the web
from helpers import isValidRelease, isValidPlat, getValgrindErrors

class GetPath(object) :

    def __init__(self, formatter, relPath, release, arch) :
        import datetime
        self.relPath = relPath
        self.release = release
        self.arch = arch
        self.prodArch = 'slc5_amd64_gcc434'
        if release[6] == "3": self.prodArch = 'slc5_ia32_gcc434' 
        self.formatter = formatter

        self.cfgInfo = None
        self.scramInfo = None
        self.pycfgInfo = None

        self.igInfo = None

    def __del__(self):
        pass

    def MakeIgnominy(self, relPath) :
        from makeDepMetrics import mkDepMetrics
        # this info is basically independent of the arch, though it's stored by arch at present.
        # so just use the main production arch for this (and list it under the "arch independent" part
        self.igInfo = mkDepMetrics(self.formatter, self.arch, self.release, relPath)
        result = self.igInfo.makeSummary()
        pkglist= self.igInfo.packlist()
        outputlist = self.igInfo.repack(pkglist)
        # if result:
        self.igInfo.dropdown(outputlist)

    def igSummary(self):
        igSumm = self.igInfo.summary.replace('Cycles', 'Nr of separate cyclic dependencies :')
        igSumm = igSumm.replace('Members', 'Nr. of packages in cyclic dependencies:')
        igSumm = igSumm.replace('Packages', 'Total nr. of packages (incl. external tools) :')
        igSumm = igSumm.replace('Levels', 'Total nr. of levels for the pacakges :')
        return igSumm
    
    def igCycles(self):
        return self.igInfo.cycles

    def igLevels(self):
        return self.igInfo.levels

    def igErrors(self):
        errRe = re.compile(r'.*?<li>\s*Cycles\s*(\d*).*', re.M|re.S)
        errMatch = errRe.match( self.igInfo.summary )
        nErr = -1
        if errMatch:
            nErr = errMatch.group(1)
        elif self.igInfo.summary:  nErr = 0
        return int(nErr)

    def isLogChanged(self,logFile,genFile):
        if not os.path.exists(logFile): return True
        if not os.path.exists(genFile): return True
        logStamp = os.path.getmtime(logFile)
        if logStamp != os.path.getmtime(genFile):
            os.system('touch -r '+logFile+' '+genFile)
            return True
        return False

    def writePickleData(self,data,pFile):
        from pickle import Pickler
        outFile = open(pFile, 'wb')
        pklFile = Pickler(outFile, protocol=2)
        pklFile.dump(data)
        outFile.close()
        return

    def readPickleData(self,pFile):
        import  pickle
        return pickle.load(open(pFile,'rb'))

    def MakeLog(self) :
        if not os.path.isdir( config.siteInfo['OutPath']+'/'+self.release) :
            os.system('mkdir -p '+ config.siteInfo['OutPath']+'/'+self.release)

        rel = config.siteInfo['OutPath']+'/'+self.release
        relarch = config.siteInfo['OutPath']+'/'+self.release+'/'+self.arch

        logFile = self.relPath+'/scramInfo.log'
        genFile = rel+'/scramInfo.html'
        if self.isLogChanged(logFile,genFile):
            from makeScramInfo import makeScramInfo
            ScramLog = makeScramInfo(logFile,rel)
            self.scramInfo = ScramLog.AnalyzeLog()
            ScramLog.closeFile()
            self.writePickleData(self.scramInfo,rel+'/scramInfo.pkl')
            self.isLogChanged(logFile,genFile)
        else: self.scramInfo = self.readPickleData(rel+'/scramInfo.pkl')

        logFile = self.relPath+'/testLogs/chkPyConf.log'
        genFile = rel+'/pyCheck.html'
        if self.isLogChanged(logFile,genFile):
            from makePyCheck import makePyCheck
            PycfgLog = makePyCheck(logFile,rel)
            self.pycfgInfo = PycfgLog.AnalyzeLog()
            PycfgLog.closeFile()
            self.writePickleData(self.pycfgInfo,rel+'/chkPyConf.pkl')
            self.isLogChanged(logFile,genFile)
        else: self.pycfgInfo = self.readPickleData(rel+'/chkPyConf.pkl')

        if not os.path.isdir(relarch): os.system('mkdir -p ' + relarch) 

class InfoMaker(object):

    def __init__(self):
        self.GP = None
        self.relPath = ""
        self.relBaseLen = len(config.siteInfo['afsPath'])


    # --------------------------------------------------------------------------------
    
    def getCRVErrors(self, arch, wkDay, stamp, release):

        crvDir = self.relPath + '/codeRules/'
        nErr = -1

        # read all pickle files and count sum of errors ...
        pklFiles = glob.glob(crvDir+'/cmsCodeRule*.dat')

        errList = {}
        for pklFileName in pklFiles:
            pklIn = open(pklFileName,'rb')
            from pickle import Unpickler
            upklr = Unpickler(pklIn)
            data = upklr.load() # { file : [lines] }
            pklIn.close()
            errList[pklFileName] = len(data.keys())
            nErr += len(data.keys())
        return nErr

    # --------------------------------------------------------------------------------
    
    def getDDErrors(self, arch, wkDay, stamp, release):
        errs = []
        total = 0
        for nfile in ["dup", "lostDefs", "edmPD"]:
            ffile = config.siteInfo['afsPath']+self.relPath[self.relBaseLen:]+'/testLogs/dupDict-'+nfile+'.log'
            cnt =-1
            if os.path.exists(ffile):
                err, out = getstatusoutput("grep -v '^Searching for ' "+ffile+" | grep -v '^\*\*\*\* SKIPPING ' | grep -v '^ *$' | wc -l")
                cnt = int(out)
                total = total + cnt
            errs.append(cnt)
        return total,errs[0],errs[1],errs[2]

    # --------------------------------------------------------------------------------

    def readRelValTimingFile(self, timingFile):
        count  = 0
        avg    = -1
        if os.path.exists(timingFile):
            try:
                xFile = open(timingFile)
                for line in xFile.readlines():
                    line = line.strip()
                    if (avg == -1) and (re.match("^Average time per workflow:\s*\d+\s*s\s*$",line)):
                        avg = int(re.sub("\s*s\s*$",'',re.sub("^Average time per workflow:\s*",'',line)))
                    elif re.match("^CMSSW_.+-Workflow.xml:\s*.+$",line): count += 1
                xFile.close()
            except Exception as e:
                print ('ERROR during '+timingFile+' file : ' + str(e))

        return count,avg
    
    # --------------------------------------------------------------------------------

    def getAppBuildSetErrors(self, appType):
        testDir = self.relPath+'/BuildSet/'+appType
        info = [ -1, None, None ]
        if os.path.exists(testDir+'/'+appType+'BuildSet.log'):
            info[0]=2
            info[1]='BuildSet/'+appType+'/'+appType+'BuildSet.log'
            if os.path.exists(testDir+'/index.html'): info[2] = 'BuildSet/'+appType+'/index.html'
            if os.path.exists(testDir+'/status'):
                inFile = open(testDir+'/status')
                status = inFile.readline()
                inFile.close()
                status = status.rstrip()
                if status == 'ok':        info[0]=0
                elif status == 'warning': info[0]=1
                elif status == 'error':   info[0]=2
                elif status == 'skip':    info[0]=3

        return info

    # --------------------------------------------------------------------------------
    
    def writeSummary(self, path, vgErrs, igErrs, ddErr, cfgInfo, dfsErr, prodErr, fwliteBS):

        try:
            from pickle import Pickler
            diffTime = 0
            if not os.path.exists(path+'/timestamp'):
                if not os.path.exists(path):
                    err, out = getstatusoutput("mkdir -p "+path)
                tsFile = open(path+'/timestamp', 'w')
                tsFile.close()
            else: diffTime = time.time() - os.path.getmtime(path+'/timestamp')

            # see if we got all info so that the readers can see if they need to refresh
            # Or too much time has passed
            allFound = True
            if (diffTime<86400):
                allFound = (igErrs > -1) and (fwliteBS>-1)
                allFound = allFound and (ddErr[0]>-1) and (ddErr[1]>-1) and (ddErr[2]>-1) and (ddErr[3]>-1)
            else:
                if fwliteBS==-1: fwliteBS=3
            summFile = open(path+'/qaSummary.pkl', 'wb')
            pklr = Pickler(summFile, protocol=2)
            pklr.dump(vgErrs)
            pklr.dump(igErrs)
            pklr.dump(ddErr)
            pklr.dump(cfgInfo)
            pklr.dump(allFound)
            pklr.dump(dfsErr)
            pklr.dump(prodErr)
            pklr.dump(fwliteBS)

            summFile.close()
            print ("Successfully pickled summary ",'<br/>')
        except Exception as e:
            print ("ERROR during pickling summary : " + str(e))

        return

    # --------------------------------------------------------------------------------
    
    def getDirFileSizeErrors(self, release, arch):
        MByte = 1024.*1024.
        dirSizeMax = 50  # MByte
        filSizeMax =  10  # MByte
        errDirSize = -1
        errFilSize = -1
        self.topDirs  = {}
        self.topFiles = {}
        try:

            # afsWebDir = os.path.join(config.siteInfo['afsPath'], 'slc5_ia32_gcc434', 'www' )
            jsonFile = os.path.join(self.relPath, 'testLogs','treeInfo-IBsrc.json')

            pklFileName = config.siteInfo['qaPath']+'/qaInfo/'+release+'-treeInfo-IBsrc.pkl'
            if not os.path.exists(pklFileName):
                try:
                    thisPath = os.path.dirname(os.path.abspath(__file__))
                except Exception as e:
                    thisPath = scriptPath
                cmd  = 'export PATH=/usr/local/bin/:$PATH;'
                cmd += thisPath+'/json2pkl.py ' + jsonFile + ' '+pklFileName
                cmd += ' >/tmp/json2pkl.log 2>&1'
                ret = os.system(cmd)

            if os.path.exists(pklFileName): # continue only if conversion is OK
                pklIn = open(pklFileName,'r')
                from pickle import Unpickler
                upklr = Unpickler(pklIn)
                data = upklr.load()
                pklIn.close()

                from operator import itemgetter
                self.topDirs  = sorted(data[1].items(), key=itemgetter(1), reverse=True)
                self.topFiles = sorted(data[2].items(), key=itemgetter(1), reverse=True)

                errDirSize = 0
                for i in range(10):
                    if float(self.topDirs[i][1]) > dirSizeMax*MByte : errDirSize += 1

                errFilSize = 0
                for i in range(10):
                    if float(self.topFiles[i][1]) > filSizeMax*MByte : errFilSize += 1
                
        except Exception as e:
            print ("Error processing dirfilesize info:", str(e),'<br/>')
            pass
            
        return errDirSize, errFilSize, dirSizeMax, filSizeMax

    # --------------------------------------------------------------------------------
    
    def showQAInfo(self):

        import getopt
        options = sys.argv[1:]
        try:
            opts, args = getopt.getopt(options, 'h',['help'])
        except getopt.GetoptError:
            usage()
            sys.exit(-2)

        from  TWikiFormatter import TWikiFormatter

        rel = None
        form = cgi.FieldStorage()
        release=''
        arch=''
        prodArch='slc5_amd64_gcc434'
        formatter = TWikiFormatter('CMSSW Integration Build QA page',"")
        if "release" in form and "arch" in form :
            release = os.path.basename(form["release"].value)
            arch = os.path.basename(form["arch"].value)

            if not isValidPlat(arch) or not isValidRelease(release):
                formatter = TWikiFormatter('CMSSW Integration Build QA page',"")
                formatter.writeH3( "ERROR: Illegal arch ("+arch+") and/or release ("+release+") given. Aborting." )
                return
        else :
            formatter.writeH3( "ERROR: no arch ("+arch+") or release ("+release+") given. Aborting." )
            return
        if release[6] == "3": prodArch = 'slc5_ia32_gcc434'
        summary = False
        if 'summaryOnly' in form :
            summary = True

        formatter = TWikiFormatter('CMSSW Integration Build QA page', release=release)

        import datetime
        import re
        rc, slhc, yr,mon,day,hr = re.search('CMSSW_(\d+_\d+|\d+_\d+_[\w\d]+)_X(_SLHC|)_(\d\d\d\d)-(\d\d)-(\d\d)-(\d\d)\d\d',release).groups()
        buildDate = datetime.date(int(yr), int(mon), int(day))
        wkDay = buildDate.strftime('%a').lower()
        stamp = rc.replace('_','.')+'-'+wkDay+'-'+hr

        self.relPath = config.siteInfo['afsPath']+'/'+arch+'/www/'+wkDay+'/'+stamp+'/'+release+'/'
        OutRel  = config.siteInfo['OutHtml']+'/'+release
        OutArch = config.siteInfo['OutHtml']+'/'+release+'/'+arch
        formatter.writeH1("CMSSW Integration Build QA Info")
        backToPortal = ' -- <a href="https://cmssdt.cern.ch/SDT/html/cmssdt-ib/">Back to IB portal</a>'
        formatter.writeH3('Integration Build '+ release + ' for architecture '+arch+backToPortal)

        # --------------------------------------------------------------------------------
        # first collect all information ...

        # prepare the plots and other info
        self.GP = GetPath(formatter, self.relPath, release, arch)
        self.GP.MakeLog()
        self.GP.MakeIgnominy(self.relPath)

        vgErrs = getValgrindErrors(release, arch)
        igErrs = self.GP.igErrors()
        ddErr  = self.getDDErrors(prodArch, wkDay, stamp, release)
        fwliteTotal = self.getAppBuildSetErrors('fwlite')

        # redo the collection for the prod arch as well if we're called for a different arch
        # but only for the items which are not architecture specific
        if arch != prodArch: 
            GP = GetPath(formatter, self.relPath, release, prodArch)
            GP.MakeLog()
            GP.MakeIgnominy(self.relPath)

        # dir and file size info:
        dfsErrs = -1
        dfsErrDir, dfsErrFil, dsMax, fsMax = self.getDirFileSizeErrors(release, arch)
        if dfsErrDir > -1 and dfsErrFil > -1:
            dfsErrs = dfsErrDir+dfsErrFil

        # ********** end of collecting info - now prepare output **********

        # if summary was requested, write pkl file and return
        #-ap: ToDo: check that we have all the info, rewrite if updates are available ...
        if summary:
            summPath = config.siteInfo['OutPath']+'/'+release+'/'+arch
            self.writeSummary(summPath, vgErrs, igErrs, ddErr, self.GP.cfgInfo, (dfsErrDir,dfsErrFil), 0,fwliteTotal[0])
            formatter.write('summary written')
            return

        # ... then set up the TOC/summary
        formatter.write('<a name="top" ></a>')

        tmsStyle = 'white'

        igString = ''
        igStyle = "passed"
        if int(igErrs) < 0:
            igStyle = 'unknown'
        elif int(igErrs) > 0:
            igStyle = 'failed'
        formatter.write('<p><a href="#ignominy" class="a'+igStyle+'">Ignominy Information</a></p>')

        ddStyle = 'passed'
        ddNum = 'No'
        if ddErr[0] < 0:
            ddStyle = 'unknown'
        elif ddErr[0] > 0:
            ddStyle = 'failed'
            ddNum = str( ddErr[0] )
        formatter.write('<p><a href="#dupDict" class="a'+ddStyle+'">Duplicate definitions of dictionaries</a></p>')

        dfsStyle = 'unknown'
        dfsNum   = 'No'
        if dfsErrs > -1 :
            dfsStyle = 'passed'
            if dfsErrs > 0:
                dfsStyle = 'failed'
                dfsNum   = '('+str( dfsErrDir )+','+str(dfsErrFil)+')'
        formatter.write('<p><a href="#dirAndFileSize" class="a'+dfsStyle+'">Directory and File size checks</a></p>')

        crvErrs = -1
        try:
            crvErrs = self.getCRVErrors(prodArch, wkDay, stamp, release)
        except:
            pass
        crvStyle = 'unknown'
        crvNum   = 'No'
        if crvErrs > -1 :
            crvStyle = 'passed'
            if crvErrs > 0:
                crvStyle = 'failed'
                crvNum   = str( crvErrs )
        formatter.write('<p><a href="#codeRules" class="a'+crvStyle+'">Code Rule Violations</a></p>')

        fwBSStyle = 'unknown'
        if fwliteTotal[0] > -1 :
            if   fwliteTotal[0] == 0: fwBSStyle = 'passed'
            elif fwliteTotal[0] == 1: fwBSStyle = 'warning'
            elif fwliteTotal[0] == 2: fwBSStyle = 'failed'
            elif fwliteTotal[0] == 3: fwBSStyle = 'skipped'
            else: fwBSStyle = 'failed'
        formatter.write('<p><a href="#FWLiteBuildSet" class="a'+fwBSStyle+'">FWLite BuildSet</a></p>')

        # ================================================================================
        # Architecture specific info
        # ================================================================================

        formatter.writeH2("Architecture dependent Information")
        formatter.write('<hr size=5px>\n')

        # ================================================================================
        # Architecture independent info
        # ================================================================================

        formatter.writeH2("Architecture Independent Information")
        formatter.write('<hr size=5px>\n')

        # --------------------------------------------------------------------------------
        formatter.writeAnchor('codeRules')
        formatter.writeH3("Information on code-rule violations", styleClass=crvStyle)

        codeRulesPage = self.relPath+'/codeRules/cmsCRPage.html'
        if not os.path.exists(codeRulesPage):
            formatter.write('<p>No info on code-rule violations available</p>')
        else:
            codeRulesPageURL = config.siteInfo['HtmlPath']+'/rc/'+self.relPath[self.relBaseLen:]+'/codeRules/cmsCRPage.html'
            formatter.write('<p>A total of '+crvNum+' files with code rules violations.</p>')
            formatter.write('<p><a href="'+codeRulesPageURL+'">Details on code-rule violations</a> </p>')

        # --------------------------------------------------------------------------------
        formatter.writeAnchor('dirAndFileSize')
        formatter.writeH3("Dir and File Size Information", styleClass=dfsStyle)
        if dfsStyle == 'unknown':
            formatter.write('No Dir and File size info available<p></p>')
        else:
            detailURL = config.siteInfo['CgiHtmlPath']+'showDirFileSize.py?release='+release;
            formatter.write('<p><a href="'+detailURL+'">Click here for more details.</a></p>')
                
            msg = "<p>"
            msg += 'Errors are defined as:<ul>'
            msg += '<li>Files with sizes larger than '+str(fsMax)+' MB</li>'
            msg += '<li>Directories with sizes larger than '+str(dsMax)+' MB</li>'
            msg += "</ul><p>"
            formatter.write(msg)
            try:
                formatter.write('<p> Top 10 directories:</p>')
                formatter.startTable(2,['dir','size [MB]'])
                MByte = 1024.*1024.
                for i in range(10):
                    formatter.writeRow([self.topDirs[i][0], str(float(self.topDirs[i][1])/MByte)])
                formatter.endTable()
            
                formatter.write('<p>Top 10 files:</p>')
                formatter.startTable(2,['dir','size [MB]'])
                for i in range(10):
                    formatter.writeRow([self.topFiles[i][0], str(float(self.topFiles[i][1])/MByte)])
                formatter.endTable()

            except Exception as e:
                formatter.write("Error loading treeInfo: "+str(e))

        # --------------------------------------------------------------------------------

        formatter.writeAnchor('FWLiteBuildSet')
        formatter.writeH3("FWLite BuildSet", styleClass=fwBSStyle)
        fwliteStr = "No information (yet?) available"
        if fwliteTotal[0] > -1:
            fwliteStr = '<ul><li><a href="'+config.siteInfo['HtmlPath']+'/rc/'+self.relPath[self.relBaseLen:]+'/'+fwliteTotal[1]+'"> FWLite Log </a></li>'
            if not fwliteTotal[2]: fwliteStr += '<li> No FWLite BuildSet information available </li></ul>'
            else: fwliteStr += '<li><a href="'+config.siteInfo['HtmlPath']+'/rc/'+self.relPath[self.relBaseLen:]+'/'+fwliteTotal[2]+'"> FWLite BuildSet information </a></li></ul>'
        formatter.write(fwliteStr)

        # --------------------------------------------------------------------------------

        formatter.writeAnchor('ignominy')
        formatter.writeH3("Ignominy Information", styleClass=igStyle)
        if igErrs < 0:
            formatter.write("No information (yet?) available")
        else:
            formatter.write(self.GP.igSummary())
            formatter.write(self.GP.igCycles())
            formatter.write(self.GP.igLevels())

        # --------------------------------------------------------------------------------

        pycfgString = ''
        pycfgStyle = "passed"
        pycfgNum   = "No"
        if not self.GP.pycfgInfo[2]:
            pycfgStyle = 'unknown'
        if self.GP.pycfgInfo[1] and len(self.GP.pycfgInfo[1]) > 0:
            pycfgStyle = 'failed'
            pycfgNum = str( len(self.GP.pycfgInfo[1]) )

        formatter.writeH3("Log file for checking Python Configuration files", styleClass=pycfgStyle)
        pycfgString += ' <a href="'+config.siteInfo['HtmlPath']+'/rc/'+self.relPath[self.relBaseLen:]+'testLogs/chkPyConf.log"'
        pycfgString += '> '+pycfgNum+' packages with old style configuration files found in release </a>'
        pycfgString += '<ul>'
        if self.GP.pycfgInfo[1] :
            for pkg in self.GP.pycfgInfo[0]:
                pycfgString += '<li> '+pkg+ '</li>'
        pycfgString += '</ul>'
 
        formatter.write(pycfgString)
#         formatter.startTable(2,['Python Configuration Checking','Graph'])
#         formatter.writeRow([pycfgString, '<img src=\"'+OutRel+'/ChkPy.png\" width=300px height=200px onclick="enlarge(this)" onmouseout="ensmall(this)" id="vmem" alt="Virtual memory info" />'])
#         formatter.endTable()
        
        # --------------------------------------------------------------------------------
        formatter.writeAnchor('dupDict')
        formatter.writeH3("Duplicate definitions of dictionaries", styleClass=ddStyle)
        formatter.startUl()
        formatter.writeLi('<a href="'+config.siteInfo['CgiHtmlPath']+'showDupDict.py/'+self.relPath[self.relBaseLen:]+'testLogs/dupDict-dup.log">'+str(ddErr[1])+' duplicate definitions of dictionaries as found in class_def.xml files</a>')
        formatter.writeLi('<a href="'+config.siteInfo['CgiHtmlPath']+'showDupDict.py/'+self.relPath[self.relBaseLen:]+'testLogs/dupDict-lostDefs.log">'+str(ddErr[2])+' definition of dictionaries in the "wrong" library</a>')
        formatter.writeLi('<a href="'+config.siteInfo['CgiHtmlPath']+'showDupDict.py/'+self.relPath[self.relBaseLen:]+'testLogs/dupDict-edmPD.log">'+str(ddErr[3])+' duplicate definitions of dictionaries as found in edmPlugins </a>')
        formatter.endUl()

    def usage(self) :
        print ('usage : ',sys.argv[0])
        print ("")
        return

if __name__ == "__main__" :

    im = InfoMaker()
    im.showQAInfo()

