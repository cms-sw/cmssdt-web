#!/usr/bin/env python

# make sure this is first to trap also problems in includes later
import os,sys,time,re,cgi
import cgitb; cgitb.enable() ## cgitb.enable(display=0, logdir=os.getcwd()+"/../cgi-logs/")

import matplot_init
import matplotlib
matplotlib.use('Agg')
from pylab import *


class makeCfgInfo(object):

    def __init__(self, logfile, outpath) :
        import config
	self.outPath = outpath
        self.logfile = logfile
	self.cfgInfo = None

    def closeFile(self):
        if self.cfgInfo:
	    self.cfgInfo.write('</body>\n</html>\n')
	    self.cfgInfo.close()
    
    def AnalyzeLog(self) :
	self.cfgInfo = open(self.outPath+'/cfgInfo.html','w')
	self.cfgInfo.write('\n')
	self.cfgInfo.write('<html>\n<head>\n<link rel="stylesheet" type="text/css" href="http://cern.ch/cms-sdt/intbld.css"><Title>Old Cfg file</Title></head><body>')
        try:
            page = open(self.logfile)
        except:
            self.cfgInfo.write('No information available for packages with old style config files\n')
            return None, None, False
        
	lines = []
        try:
            lines = page.readlines()
            page.close()
        except:
            self.cfgInfo.write("no log\n")
            pass
	#print "makeCfgInfo analyzeLogFile start!"
        cfgInfo = {}
	prePkg=''
        for line in lines:
            try:
                pkg, num = line.split(':')
                if num.strip() == '0': continue
                cfgInfo[pkg] = num
            except:
                raise
            
        pkgList = cfgInfo.keys()
	labels=[]
	fracs=[]
        if len(pkgList) > 0:
            self.cfgInfo.write('Found a total of '+str(len(pkgList))+' packages with old style config files\n')
            self.cfgInfo.write('<table border="1">\n<tr><th><b>Package</b></th><th><b># of Old style Config file</b></th></tr></thead><tbody>\n') 
            pkgList.sort()
	    prepkg=''
            for pkg in pkgList:
		if prepkg.split('/')[0]==pkg.split('/')[0] :
			fracs[-1]=fracs[-1]+int(cfgInfo[pkg])
		else :
			prepkg = pkg
			labels.append(pkg.split('/')[0].replace('_','\n'))
			fracs.append(int(cfgInfo[pkg]))
                err = cfgInfo[pkg]
                self.cfgInfo.write('<tr><td>'+pkg.strip()+'</td><td>  '+ str(err).strip()+'</td></tr>\n')
        else:
            self.cfgInfo.write('<h1>No packages with old style config files found.</h1>\n')
	
	self.cfgInfo.write('<img src="cfgInfo.png" alt="Angry face" align="right" width=500 height=500 />')

	self.makePie(labels,fracs)
	#print 'makeCfgInfo analyzeLogFile end!'
        return labels, fracs, True

    def makePie(self,labels,fracs):
	#figure(1,figsize=(9,9))
	#ax= axes([0.2,0.2,0.7,0.7])
	pie(fracs, labels=labels, autopct='%1.1f%%',shadow=True)
	title('Old Cfg',bbox={'facecolor':'0.8','pad':5})
	savefig(self.outPath+'/cfgInfo.png',format='png')
	cla()
	

if __name__ == '__main__' :
   pass 
