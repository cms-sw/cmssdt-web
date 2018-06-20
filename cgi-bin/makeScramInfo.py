#!/usr/bin/env python

# make sure this is first to trap also problems in includes later

import os, sys, time, re,cgi
import cgitb; cgitb.enable() ## cgitb.enable(display=0, logdir=os.getcwd()+"/../cgi-logs/")



class makeScramInfo(object):

    def __init__(self, logfile, outpath ):
        import config
	self.scramInfo = None
	self.logfile = logfile
	self.outPath = outpath

    def closeFile(self):
        if self.scramInfo:
	    self.scramInfo.write('</body>\n</html>\n')
	    self.scramInfo.close()
    
    # --------------------------------------------------------------------------------

    def AnalyzeLog(self):
	self.scramInfo = open(self.outPath+'/scramInfo.html','w')
	self.scramInfo.write('\n')
	self.scramInfo.write('<html>\n<head>\n<link rel="stylesheet" type="text/css" href="http://cern.ch/cms-sdt/intbld.css"><Title>SCRAM Infomation</Title></head><body>\n')
	lines = []
        try:
            page = open(self.logfile)
        except:
            return None, None

        try:
            lines = page.readlines()
            page.close()
        except:
            self.scramInfo.write("no log\n")
            return
        scramErrRe  = re.compile('^\s*\*+\s*ERROR: .*?\s*src/([A-Z].*?/[A-Z].*?)/.*')
        scramWarnRe = re.compile('^\s*\*+\s*WARNING: .*?\s*src/([A-Z].*?/[A-Z].*?)/.*')
        scramExErrRe  = re.compile('^\s*\*+\s*ERROR:.*')
        scramExWarnRe = re.compile('^\s*\*+\s*WARNING:.*')
        prepkg=''
        errPkg  = {}
        warnPkg = {}
        startFound = False
        linesOut = []
        nErr = 0
        nWarn = 0
        for line in lines:
            if "Resetting caches" in line: startFound = True
            if not startFound: continue
            linesOut.append(line)
            
            sMatch = scramErrRe.match(line)
            if sMatch :
                nErr += 1
                pkg = sMatch.group(1)
                if pkg not in errPkg :
                    errPkg[pkg] = 1
                else:
                    errPkg[pkg] += 1
                continue
                    
            sMatch = scramWarnRe.match(line)
            if sMatch :
                nWarn += 1
                pkg = sMatch.group(1)
                if pkg not in warnPkg :
                    warnPkg[pkg] = 1
                else:
                    warnPkg[pkg] += 1
                continue

            sMatch = scramExErrRe.match(line)
            if sMatch :
                nErr += 1
                continue
                    
            sMatch = scramExWarnRe.match(line)
            if sMatch :
                nWarn += 1
                continue

        pkgList = errPkg.keys()
        if nErr > 0:
            self.scramInfo.write('---+A total of '+str(nErr)+' SCRAM errors in '+str(len(pkgList))+' packages found in build.\n')
            self.scramInfo.write('|  *Package*  |  *Scram Errors*  |\n')
            pkgList.sort()
            for pkg in pkgList:
                err = errPkg[pkg]
		if pkg==prepkg :
			self.scramInfo.write('|  ^  |  '+str(err)+'  |\n')
		else :
                	self.scramInfo.write('|  !'+pkg+'  |  '+ str(err)+'  |\n')
		prepkg=pkg
        else:
            self.scramInfo.write('<h1>No SCRAM errors found in build.</h1>\n')

        pkgList = warnPkg.keys()
        if nWarn > 0:
            self.scramInfo.write('---+A total of '+str(nWarn)+' SCRAM warnings in '+str(len(pkgList))+' packages found in build.\n')
            self.scramInfo.write('|  *Package*  |  *Scram Warnings*  |\n')
            pkgList.sort()
            for pkg in pkgList:
                warn = warnPkg[pkg]
		if pkg == prepkg :
			self.scramInfo.write('|  ^  |  '+str(warn)+'  |\n')
		else :
                	self.scramInfo.write('|  !'+pkg+'  |  '+ str(warn)+'  |\n')
		prepkg=pkg
        else:
            self.scramInfo.write('<h1>No SCRAM warnings found in build.</h1>\n')

        return errPkg, warnPkg

if __name__ == '__main__' :
	pass 

 


