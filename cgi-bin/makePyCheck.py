#!/usr/bin/env python
import urllib2, re, os, sys,cgi
import cgitb; cgitb.enable() ## cgitb.enable(display=0, logdir=os.getcwd()+"/../cgi-logs/")

class makePyCheck(object) :
    def __init__(self,logfile,outpath) :
	import config
	self.outPath= outpath
	self.logfile = logfile
	self.PyInfo = None
 
    def closeFile(self) :
        if self.PyInfo:
	    self.PyInfo.write('</body>\n</html>\n')
	    self.PyInfo.close()
	
    def AnalyzeLog(self) :
	self.PyInfo = open(self.outPath+'/pyCheck.html','w')
	self.PyInfo.write('\n')
	self.PyInfo.write('<html>\n<head>\n<link rel="stylesheet" type="text/css" href="http://cern.ch/cms-sdt/intbld.css"><Title>Checking Python Configuration file</Title></head><body>')
	current_pkg=''
       	pkg = {}
	try : 
		lines=open(self.logfile)
	except :
		return None, None, False
		
	for line in lines :
            if(len(line)==1) :
		break
            if line.split()[0] == 'Package:' :
                current_pkg=line.split()[1]
                pkg[current_pkg]=[]
            elif line.split()[0] == 'missing' or line.split()[0]=='update' :
                pkg[current_pkg].append( line.split()[-1].split('/')[-1][:-3])
	    else :
                continue

        labels=[]
        for x in pkg.keys():
            labels.append(x.replace('_','\n')) 
	fracs=[]
	for x in pkg.keys() :
            fracs.append(len(pkg[x]))
	return labels, fracs, True

