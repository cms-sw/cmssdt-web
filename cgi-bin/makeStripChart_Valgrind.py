#!/usr/local/bin/python2.6
import os, re, sys
import math
import matplotlib
import pylab
import config
from helpers import getReleaseSeries

# sys.path.append('/usr/local/lib/python2.6/site-packages/couchdbkit-0.4.6-py2.6.egg')
from couchdbkit import *
import urllib2

class makeStripChart(object) :
    def __init__(self, rel,arch,outpath):
	#arch=arch.replace('amd64','ia32') # amd64 is not support
	self.outPath=outpath
	self.arch=arch
        self.rel=getReleaseSeries(rel)
	 
    def mkStripChart(self) :

###
# Make dup dict strip charts
###
        data={'title':[], 'vgerror':[]}
        server = Server()
        db = server.get_or_create_db("testdb")
        sk=[self.arch,self.rel,"showIBvg",["00","00","00","00"]]
        ek=[self.arch,self.rel,"showIBvg",["99","99","99","99"]]
        results = db.view("apps/by_release_filename",obj=None, wrapper=None,startkey=sk,endkey=ek)
        titleold=''
        for result in results:
#                print result
                ymdh=result['value'][3].split('-')
                title=ymdh[1]+'-'+ymdh[2]+'-'+ymdh[3][0]+ymdh[3][1]+'00'
                if title==titleold :
                        db.delete_doc(result['id'])
                else:
                        data['title'].append(title)
                        data['vgerror'].append(float(result['value'][4]['vgerror']))
                        titleold=title
#               print data['title']
        if len(data) ==0 :
                return False
        if len(data['title'])==0 :
                return False
#	print data
        import matplotlib.pyplot as plt
        ind=range( len(data['title']) )
        if len(data['title'])>10 :
            for x in ind :
                if x%10!=0 :
                    data['title'][x]=''

        plot, axs = plt.subplots(nrows=1)
        plot.suptitle('Valgrind')
        ax = axs
        ax.set_xticks(ind)
        ax.set_xticklabels( data['title'],rotation=15,size='xx-small')
        ax.plot( data['vgerror'], '-o',label='Errors')
        ax.set_ylim( ymax=max(data['vgerror'])+2.0 ,ymin=min(data['vgerror'])-1.0 )
        ax.legend(loc=0)
        pylab.savefig(self.outPath+'/29.png',format='png')



def getLatestIB(cycle):

    import time
    tgtDir = ''
    latest = 9999999
    now = time.time()
    host,domain = config.getHostDomain()
    ibTopDir = config.sitesInfo[host]['OutPath'] 
    for ibDir in os.listdir( ibTopDir ):
        if not ibDir.startswith(cycle): continue
        statinfo = os.stat(  os.path.join(ibTopDir,ibDir) )
        if now - statinfo.st_ctime < latest:
            latest = now - statinfo.st_ctime
            tgtDir = os.path.join(ibTopDir,ibDir) 

    return tgtDir

if __name__=="__main__" :

    arch = "slc5_amd64_gcc434"
    cycle = "CMSSW_4_2_X"
    tgtDir = os.path.join( getLatestIB(cycle), arch)

    mbn = makeStripChart(cycle,arch,tgtDir)
    mbn.mkStripChart()

    
    
