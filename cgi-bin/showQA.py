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

class QADisplay(object):

    def __init__(self, fmtr):
        self.formatter = fmtr
        

    def checkIBString(self, ib):
        reIB = re.compile('^CMSSW_\d+_\d+(_.+|)_X_\d\d\d\d-\d\d-\d\d-\d\d\d\d$')
        return reIB.match(ib)

    def checkArchString(self, arch):
        reArchSLC = re.compile('^slc\d_(ia32|amd64)_gcc[34]\d\d$')
        reArchMac = re.compile('^osx\d\d\d_(ia32|amd64)_gcc4\d\d$')
        return reArchSLC.match(arch) or reArchMac.match(arch)
    
    # --------------------------------------------------------------------------------

    def showInfo(self):

        self.formatter.writeAnchor(ref='top')
        self.formatter.writeH2("CMSSW Integration Build QA Info ")

        pathReq = ""
        try:
            scriptName = os.environ["SCRIPT_NAME"]
            requestURI = os.environ["REQUEST_URI"]
            pathReq = cleanPath( requestURI.replace(scriptName,'') )
        except:
            pathReq = sys.argv[1]
            pass

        topLogDir = config.siteInfo['afsPath']
        fullPath = topLogDir + pathReq
        normPath = os.path.normpath( fullPath )

        logBaseURL = config.siteInfo['HtmlPath']+'/rc'

        ib = normPath.split('/')[-1]
        if not self.checkIBString(ib):
            print "Illegal IB found ! : ", ib
            return

        arch = pathReq.split('/')[1]
        if not arch:
            arch = 'slc4_ia32_gcc345'
        if not self.checkArchString(arch):
            print "Illegal arch found ! : ", arch
            return
        
        self.formatter.writeH3('Integration Build ' + ib + ' for architecture ' + arch)

        qaInfoScripts = { 'scramInfo'        : 'cgi-bin/showScramInfo.py%s/%s.log' % (pathReq , '%s') ,
                          'cfgInfo'          : 'cgi-bin/showCfgInfo.py%s/%s.log'   % (pathReq , '%s') ,
                          'checkDoc'         : 'cgi-bin/checkDocProxy.py?inPath=%s/src' % normPath.replace('www/',''),
                          'dupDict-dup'      : 'cgi-bin/showDupDict.py/%s/testLogs/%s.log' % (pathReq , '%s') ,
                          'dupDict-lostDefs' : 'cgi-bin/showDupDict.py/%s/testLogs/%s.log' % (pathReq , '%s') ,
                          'dupDict-edmPD'    : 'cgi-bin/showDupDict.py/%s/testLogs/%s.log' % (pathReq , '%s') ,
                          'newPerf'          : 'cgi-bin/showNewPerf.py?ib=%s' % (ib , ) ,
                          'valgrind'         : 'cgi-bin/showValgrind.py?ib=%s' % (ib , ) ,
                          'pyCfgCheck'       : 'rc/%s/testLogs/chkPyConf.log' % (pathReq ,) ,
                          'buildLog'         : 'rc/%s/../fullLog' % (pathReq ,) ,
                          'prebuildLog'      : 'rc/%s/prebuild.log' % (pathReq ,) ,
                          'testLogDir'       : 'rc/%s/testLogs/' % (pathReq ,) ,
                          }

        qaInfoDesc = { 'scramInfo' : 'Info on scram warnings and errors',
                       'cfgInfo'   : 'Number of old-style configuration files (*.cff, *.cfi, *.cfg) in release',
                       'checkDoc'  : 'Status of documentation for each subsystem and package (takes a while)',
                       'dupDict-dup'      : 'Duplicate definitions of dictionaries as found in class_def.xml files',
                       'dupDict-lostDefs' : 'Definition of dictionaries in the "wrong" library',
                       'dupDict-edmPD'    : 'Duplicate definitions of dictionaries as found in edmPlugins',
                       'newPerf'          : 'Info of new (limited scope) performance suite',
                       'valgrind'         : 'Info of valgrind results from perfsuite',
                       'pyCfgCheck'       : 'Log file for checking Python Configuration files',
                       'buildLog'         : 'Log file from the BuildManager (check here if something _completly_ fails).',
                       'prebuildLog'      : 'Log file from "scram p" and CVS checkout.',
                       'testLogDir'       : 'Directory listing for the test logs (unit-tests, all raw test logs)',
                       }


        # keep the list separate to control the order of appearance
        qaInfoKeys = ['scramInfo', 'cfgInfo', 'pyCfgCheck', 'newPerf',
                      'dupDict-dup', 'dupDict-lostDefs', 'dupDict-edmPD',
                      'buildLog', 'prebuildLog', 'testLogDir',
                      'checkDoc',]

        qaHeader = {'scramInfo'        : 'Info on scram warnings and errors',
                    'cfgInfo'          : 'Number of old-style configuration files', 
                    'checkDoc'         : 'Status of documentation', 
                    'dupDict-dup'      : 'Duplicate definitions of dictionaries',
                    'pyCfgCheck'       : 'Log file for checking Python Configuration files',
                    'buildLog'         : 'Log file from the BuildManager',
                    'testLogDir'       : 'Directory listing for the test logs',
                    'newPerf'          : 'Info of new (limited scope) performance suite',
                    'valgrind'         : 'Info of valgrind results from perfsuite',
                    }


        import urllib2
        # first show Ignominy:
        igUrlHost = 'https://macms01.cern.ch/'
        igURL = igUrlHost+'cgi-bin/ap/showIgRun.py'
        igInfoUrl = urllib2.urlopen(igURL+'?txt=1')
        igInfo = igInfoUrl.readlines()

        link = "None"
        for line in igInfo:
            if ib in line:
                link = line
                break

        self.formatter.writeH2("Ignominy information ")
        if link == "None":
            self.formatter.write('Ignominy results not available.')
        else:
            url = igUrlHost+'ap/ignominy/'+link+'/igRun/'
            self.formatter.write('<a href="'+url+'"> Ignominy results </a>')

        # ... the timing results
        tmUrlHost = 'https://macms01.cern.ch/'
        tmURL = tmUrlHost+'cgi-bin/ap/showTimeMemInfo.py'
        tmReq = '?rel='+ib[:11]+'&arch='+arch
        tmInfoUrl = urllib2.urlopen(tmURL+tmReq)
        tmInfo = tmInfoUrl.readlines()

        self.formatter.writeH2("Timing/Memory/FileSize information ")
        if 'Error no info available for' in ' '.join(tmInfo):
            self.formatter.write('Timing/Memory results not available at '+tmURL+tmReq)
        else:
            self.formatter.write('<p>Using the timing/memory services on the Production MinBias and TTbar RelVals (1 and 2 in cmsDriver_standard_hlt.txt). File size as reported by operating system.</p>')
            url = tmURL
            self.formatter.write('<a href="'+url+tmReq+'"> Timing/Memory results </a>')

        # ... the performance suite
        psUrlHost = 'https://macms01.cern.ch/'
        psURL = psUrlHost+'cgi-bin/ap/showNewPerf.py'
        psInfoUrl = urllib2.urlopen(psURL+'?ib='+ib+'&arch='+arch)
        psInfo = psInfoUrl.readlines()

        self.formatter.writeH2("Results from (limited) performance suite")
        if 'Error no info available for' in ' '.join(psInfo):
            self.formatter.write('<p>Results for limited performance suite are not (yet?) available.</p>')
        else:
            self.formatter.write('<p>Limited (for IB) performance suite results.</p>')
            url = psURL
            self.formatter.write('<a href="'+url+'?ib='+ib+'&arch='+arch+'"> Performance suite results </a>')

        # ... valgrind
        psUrlHost = 'https://macms01.cern.ch/'
        psURL = psUrlHost+'cgi-bin/ap/showValgrind.py'
        psInfoUrl = urllib2.urlopen(psURL+'?ib='+ib+'&arch='+arch)
        psInfo = psInfoUrl.readlines()

        if 'Error no info available for' in ' '.join(psInfo):
            self.formatter.write('Valgrind results not available.')
        else:
            url = psURL
            self.formatter.write('<a href="'+url+'?ib='+ib+'&arch='+arch+'"> Valgrind results </a>')

        # ... navigator
        navMsg = '<br/> <br /> Detailed results from the (limited performance suite are available on '
        navMsg += '<a href="http://cern.ch/cms-sdt/qa/igprof/navigator">the navigator page.</a>'
        self.formatter.write(navMsg)

        # .... then the others ... 
        for val in qaInfoKeys:

            anchor = qaInfoDesc[val]
            ref    = qaInfoScripts[val]
            
            infoItem = ' N/A '
            logFile = ref
            if '%s' in ref:
                logFile = ref % val

            infoItem  = anchor + ' <a href="http://cern.ch/cms-sdt/'+logFile+'">'
            infoItem += ' '+val+' </a>'

            try:
                self.formatter.writeH2(qaHeader[val])
            except:
                pass
            
            afsLogFile = os.path.join(topLogDir, logFile).replace('rc/','')
            afsLogFile = re.sub(r'cgi-bin/.*\.py/', '/', afsLogFile)
            # print afsLogFile+'<br />'
            if not val == 'checkDoc' and not os.path.exists( afsLogFile ) :
                self.formatter.write('No information available at'+afsLogFile)
            else:
                self.formatter.write(infoItem+'<br />')


        return


def main():

    
    style = """
    <link rel="stylesheet" type="text/css" href="%s/intbld.css">\n
    """ % (config.siteInfo['HtmlPath'])

    fmtr = Formatter.SimpleHTMLFormatter(title="CMSSW Integration Build Scram Info", style=style)

    qad = QADisplay(fmtr)
    qad.showInfo()

if __name__ == '__main__' :
    main()
    
