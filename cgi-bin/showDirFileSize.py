#!/usr/bin/env python3

import os, sys, glob, cgi
import cgitb; cgitb.enable() ## cgitb.enable(display=0, logdir=os.getcwd()+"/../cgi-logs/")

# get the helpers to check the inputs from the web
from helpers import isValidRelease, isValidPlat

from tempfile import mkdtemp

import config

form = cgi.FieldStorage()
release = 'no rel given' # 'CMSSW_3_8_X_2010-06-10-0200'
prodArch='slc5_amd64_gcc434'

if "release" in form:
    release = form["release"].value
if not isValidRelease(release):
    print ("Content-Type: text/html" + '\n\n')     # HTML is following
    print ('<html><head><title>ERROR</title></head><body><h2>Error, illegal (or no) release specified :'+release+'</h2></body></html>')
    sys.exit()

scriptPath = os.path.normpath( os.path.split( os.path.abspath(sys.argv[0]) )[0] )
tmpl = open(scriptPath+'/../html/dirFileSize.htmpl','r')
lines = tmpl.readlines()
tmpl.close()

afsTopDir = config.siteInfo['afsPath']
afsWebDir = os.path.join(afsTopDir, prodArch, 'www' )

cycles = ['4.3']
for cyc in cycles:
    files = glob.glob(afsWebDir+'/*/'+cyc+'*/'+release+'/testLogs/*json')
    # print 'found ',files

    for jsonFile in files:
        release = jsonFile.split('/')[-3]
        tmpDir = mkdtemp()
        if not os.path.exists(tmpDir):
            os.mkdirs(tmpDir)
        tmpFile = tmpDir+'/json2pkl.log'
        pklFileName = config.siteInfo['qaPath']+'/qaInfo/'+release+'-treeInfo-IBsrc.pkl'
        if not os.path.exists(pklFileName):
            cmd = ''
            cmd += 'export PATH=/usr/local/bin/:$PATH;'
            cmd += scriptPath+'/json2pkl.py ' + jsonFile + ' '+pklFileName
            cmd += ' >'+ tmpFile +' 2>&1'
            ret = os.system(cmd)
            if ret != 0:
                print ("ERROR converting ", jsonFile)
                print ("      cmd used : ", cmd)
            else:
                os.system('rm -rf '+tmpDir)

msg = "Content-Type: text/html" + '\n\n'     # HTML is following
msg += "".join(lines)
msg = msg.replace('@@IB@@', release)
print (msg)
