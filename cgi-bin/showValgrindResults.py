#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Andreas Pfeiffer on 2009-04-01.
Copyright (c) 2009 CERN. All rights reserved.
"""
import cgi
import cgitb; cgitb.enable()

import sys
import os, stat, glob, re

import config

from Formatter import SimpleHTMLFormatter

def readSummFile(basePath, part='1of2'):

    import pickle
    try:
        errMapNew = {}
        rel = 'unknown' ; arch = 'unknown'
        for file in glob.glob(basePath+'/valgrindSummary-*of*.pkl'):
            summFile = open(file, 'rb')
            rel, arch = pickle.load(summFile)
            errMap = pickle.load(summFile)
            summFile.close()
            for key, val in errMap.items():
                key = re.sub('^newPerf-\d+of\d+/','',key)
                path = "/".join( key.split('/')[0:2] )+'/'
                errMapNew[path] = val
        return errMapNew, rel, arch
    except Exception, e:
        return "unknown", "unknown", "unknown"

def getCmdErr(path, sample):

    if "PILEUP" in sample:
        sample = sample.replace(' PILEUP', '')
        
    lines = os.popen('grep cmsDriver.py '+path+'/'+sample+'.log').readlines()

    cmdRe = re.compile('.*(cmsDriver.py .*?)>\&.*')
    cmdMatch = cmdRe.match(''.join(lines))
    cmd = ""
    if cmdMatch:
        cmd = cmdMatch.group(1)
    # else:
    #     print 'no match found in '+path+'/'+sample+'.log'
    #     print 'lines =', lines
    #     print '<br/>'

    return cmd


class VGResults(object):
    def __init__(self, arch, build, fmtr):

        self.plat  = arch
        self.build = build
        self.fmtr  = fmtr
        
        self.errSumm = {}
        self.indexMap = {}
        self.totErr = 0
        
        self.cmdMap = {}
        self.allLogs = {}
        
        self.errMsg = []

        self.haveRealData = False

        self.setup()

    # --------------------------------------------------------------------------------
    
    def setup(self):
        # set up
        self.pmDirs = ['newPerf-1of2', 'newPerf-2of2']
        if '3_5_X' in self.build or '3_6_X' in self.build:
            self.pmDirs = ['perfNew-1', 'perfNew-2']

        self.baseDir = config.siteInfo['qaPath'] 
        self.baseURL = config.siteInfo['HtmlPath'] 
        self.baseURLcgi = config.siteInfo['macms01Path']  

        self.afsBasePath = config.siteInfo['afsPath']  
    
        if ( not os.path.exists( os.path.join(self.baseDir, self.pmDirs[0], self.plat, self.build, self.pmDirs[0]) ) and
             not os.path.exists( os.path.join(self.baseDir, self.pmDirs[1], self.plat, self.build, self.pmDirs[1]) ) ) :
            self.fmtr.write("Error no info available for "+self.build+' on '+self.plat)
            return
    
        self.fmtr.writeH2("Valgrind reports for " + self.build + ' on ' + self.plat )

        self.pathMap = {
        "GEN-DIGI2RAW/cpu5/"  : "TTbar GEN-DIGI2RAW Valgrind results" ,
        "GEN-DIGI2RAW/cpu6/"  : "TTbar PILEUP GEN-DIGI2RAW Valgrind results" ,
        "GEN-FASTSIM/cpu5/"       : "TTbar FASTSIM  Valgrind results"      ,
        "GEN-FASTSIM/cpu6/"       : "TTbar PILEUP FASTSIM Valgrind results"      ,
        "HLT/cpu5/"           : "TTbar HLT Valgrind results"           ,
        "HLT/cpu6/"           : "TTbar PILEUP HLT Valgrind results"           ,
        "RAW2DIGI-RECO/cpu5/" : "TTbar RAW2DIGI-RECO Valgrind results" , 
        "RAW2DIGI-RECO/cpu6/" : "TTbar PILEUP RAW2DIGI-RECO Valgrind results" ,
        "RAW2DIGI-RECO/cpu7/" : "run2010A RAW2DIGI-RECO Valgrind results" ,
        "RAW2DIGI-RECO-DQM/cpu7/" : "run2010A RAW2DIGI-RECO-DQM Valgrind results" ,
        }
        self.pathMap2 = {
        "TTbar GEN-DIGI2RAW Valgrind results"         : "GEN-DIGI2RAW/cpu5/"  ,
        "TTbar PILEUP GEN-DIGI2RAW Valgrind results"  : "GEN-DIGI2RAW/cpu6/"  ,
        "TTbar FASTSIM Valgrind results"              : "GEN-FASTSIM/cpu5/"       ,
        "TTbar PILEUP FASTSIM Valgrind results"       : "GEN-FASTSIM/cpu6/"       ,
        "TTbar HLT Valgrind results"                  : "HLT/cpu5/"           ,
        "TTbar PILEUP HLT Valgrind results"           : "HLT/cpu6/"           ,
        "TTbar RAW2DIGI-RECO Valgrind results"        : "RAW2DIGI-RECO/cpu5/" ,
        "TTbar PILEUP RAW2DIGI-RECO Valgrind results" : "RAW2DIGI-RECO/cpu6/" ,
        "run2010A RAW2DIGI-RECO Valgrind results" : "RAW2DIGI-RECO/cpu7/" ,
        "run2010A RAW2DIGI-RECO-DQM Valgrind results" : "RAW2DIGI-RECO-DQM/cpu7/" ,
        }
        
        if '3_5_X' in self.build or '3_6_X' in self.build:
            self.pathMap = {
            "GEN-DIGI2RAW/cpu5/"  : "TTbar GEN-DIGI2RAW Valgrind results" ,
            "GEN-DIGI2RAW/cpu6/"  : "TTbar PILEUP GEN-DIGI2RAW Valgrind results" ,
            "FASTSIM/cpu5/"       : "TTbar FASTSIM  Valgrind results"      ,
            "FASTSIM/cpu6/"       : "TTbar PILEUP FASTSIM Valgrind results"      ,
            "HLT/cpu5/"           : "TTbar HLT Valgrind results"           ,
            "HLT/cpu6/"           : "TTbar PILEUP HLT Valgrind results"           ,
            "RAW2DIGI-RECO/cpu4/" : "TTbar RAW2DIGI-RECO Valgrind results" , 
            "RAW2DIGI-RECO/cpu5/" : "TTbar PILEUP RAW2DIGI-RECO Valgrind results" ,
            }
            self.pathMap2 = {
            "TTbar GEN-DIGI2RAW Valgrind results"         : "GEN-DIGI2RAW/cpu5/"  ,
            "TTbar PILEUP GEN-DIGI2RAW Valgrind results"  : "GEN-DIGI2RAW/cpu6/"  ,
            "TTbar FASTSIM Valgrind results"              : "FASTSIM/cpu5/"       ,
            "TTbar PILEUP FASTSIM Valgrind results"       : "FASTSIM/cpu6/"       ,
            "TTbar HLT Valgrind results"                  : "HLT/cpu5/"           ,
            "TTbar PILEUP HLT Valgrind results"           : "HLT/cpu6/"           ,
            "TTbar RAW2DIGI-RECO Valgrind results"        : "RAW2DIGI-RECO/cpu4/" ,
            "TTbar PILEUP RAW2DIGI-RECO Valgrind results" : "RAW2DIGI-RECO/cpu5/" ,
            }

    # --------------------------------------------------------------------------------
    
    def readXMLFiles(self):
        ok = False
        for pmDir in self.pmDirs:
            relPath = os.path.join(pmDir, self.plat, self.build, pmDir)
            try:
                os.chdir( os.path.join(self.baseDir, relPath) )
            except OSError:
                continue
            
            vgFiles = glob.glob('*/cpu?/*/*vlgd.xml')
            vgFiles += glob.glob('*/cpu7/*vlgd.xml') 
            for itemIn in vgFiles :
                item = itemIn
                detailItem = itemIn.replace('_vlgd.xml','_vlgd-1.xml')
                if os.path.exists(detailItem):
                    item = detailItem
                if '/cpu7/' in detailItem :
                    self.haveRealData = True
                self.indexMap[item] = os.path.join(self.baseDir, relPath)

            # read in error summaries
            self.errSumm[os.path.join(self.baseDir, relPath)] = readSummFile(os.path.join(self.baseDir, relPath))
            try:
                for k,v in self.errSumm[ os.path.join(self.baseDir, relPath) ][0].items():
                    self.totErr += abs(int(v))
                    ok = True
            except Exception, e:
                self.totErr = -1
                self.fmtr.write("No summary info found for "+os.path.join(self.baseDir, relPath)+' ?!?! <br />')
                pass
        if not ok: self.totErr = -1

    # --------------------------------------------------------------------------------
    
    def getCommands(self):
        for pmDir in self.pmDirs:
            relPath = os.path.join(pmDir, self.plat, self.build, pmDir)
            try:
                os.chdir( os.path.join(self.baseDir, relPath) )
            except OSError:
                self.errMsg.append( 'cannot chdir to '+os.path.join(self.baseDir, relPath) )
                continue

            logFiles = glob.glob('*/cpu?/*/*__*valgrind.log')
            logFiles += glob.glob('*/cpu7/*__*valgrind.log')
            for itemIn in logFiles :
                item = itemIn
                detailLog = itemIn.replace('valgrind.log','valgrind-1.log')
                if os.path.exists(detailLog): item = detailLog
                pathName,fileName = os.path.split(item)
                vgCmd = "unknown"
                cmd = 'grep cmsDriver.py '+pathName+'/*log | cut -d" " -f3- '
                try:
                    pipe = os.popen(cmd,'r')
                    vgCmd = pipe.readlines()[0]
                    pipe.close()
                except Exception, e:
                    # self.errMsg.append("Error from pipe cmd='" + cmd +"' got:"+ str(e) )
                    vgCmd = 'unknown'

                # print 'checking '+pathName+ '<br />'
                # print '<b>vgCmd</b> = ' + str(vgCmd) + '<br /><br />'
                self.cmdMap[pathName] = vgCmd
                self.allLogs[pathName] = item
    
        # for k,v in self.cmdMap.items():
        #     print k,v,'<br />'

        # for k,v in self.allLogs.items():
        #     print k,' -- ',v,'<br />'

    # --------------------------------------------------------------------------------
    
    def getAltCmd(self, step, index, sample):

        (st, cpu, lfIn) = index.split('/')
        
        relPath = os.path.join(self.afsBasePath, self.plat)
        logFiles = glob.glob(relPath+'/*/*/'+self.build+'/qaLogs/*perfNew-*.log')            
        if not logFiles:
            self.errMsg.append('Log file to extract command for real data valgrind not yet availalbe.')
        cmdRe = re.compile('.*%s\s*(cmsDriver.py\s.*%s__%s_memcheck_valgrind\.xml.*?)\>.*' %(cpu,sample,step))
        vgCmd = "unknown"
        for itemIn in logFiles :
            item = itemIn
            pathName,fileName = os.path.split(item)
            lf = open(itemIn)
            lines = lf.readlines()
            lf.close
            found = False
            for line in lines:
                cmdMatch=cmdRe.match(line)
                if cmdMatch:
                    vgCmd = cmdMatch.group(1)
                    found = True
                    break
            if not found: continue
            mapIndex = step+'/'+cpu+'/'+sample+'_memcheck'

            self.cmdMap[mapIndex] = vgCmd
            self.cmdMap[mapIndex+'_vlgd.xml'] = vgCmd
            break

        return vgCmd
        
    # --------------------------------------------------------------------------------
    
    def writeTable(self, samples, steps) :

        from helpers import getWallClockTimes
        wct,errLines = getWallClockTimes(self.build,self.plat)

        self.fmtr.startTable([5*(len(samples)+1)], [' ']+samples)
        for step in steps:
            row = [step]
            for sample in samples:
                cell = ''
                what = ' '.join([sample,step,'Valgrind results'])
                if what not in self.pathMap2.keys(): 
                    self.errMsg('ignoring non existent key for pathMap2 '+what+'<br/>')
                    continue
                path = self.pathMap2[what].replace('REL', self.build)

                vgCmd = 'unknown'
                try:  # log files may not exist yet ...
                    index = self.pathMap2[what]+sample.replace(' PILEUP','_PU')+'_Memcheck'
                    vgCmd = self.cmdMap[ index ]
                except:
                    try:
                        vgCmd = self.getAltCmd(step, index, sample)
                    except Exception, e:
                        self.errMsg.append( "Error trying to get alternate cmd for "+index+' got:'+str(e)+'<br>')
                #if vgCmd == 'unknown':
                #    self.errMsg.append( "cmd not found for "+index+'<br>')

                if 'cpu7' in index:
                    index = index.replace('_Memcheck', '_memcheck_vlgd.xml')
                
                # need to find the correct 'item' which contains the path
                for item in self.indexMap.keys():
                    if path not in item : 
                        continue
                        
                    try:
                        nerr = self.errSumm[self.indexMap[item]][0][path]
                    except TypeError:
                        nerr = -2
                    except KeyError:
                        nerr = -3
                        
                    cell = ""
                    if nerr == 0:
                        cell += '<a class="passed"> &nbsp; </a> &nbsp; '
                    else:
                        cell += '<a class="failed"> &nbsp; </a> &nbsp; '
                    cell += '<font size="+1">'+str(nerr)+' errors </font>'
                    cell += '<a href='+self.baseURLcgi+'showValgrindFile.py?'+self.indexMap[item].replace(self.baseDir,'')+'/'+item+'> '
                    cell += os.path.split(item)[1]
                    cell +=' </a> <br />'
                    cell += '<em>command used:</em> <br /> <code> '+vgCmd+' </code>'
                    elapTime = "unknown"
                    try:
                        elapTime = wct[self.pathMap2[what][:-1]]
                    except KeyError:
                        pass
                    cell += '<br /><em>elapsed time to run command:</em> '+elapTime

                # empty cell so far, link to log file
                if cell == '' or nerr < 0:
                    if what not in self.pathMap2.keys(): 
                        self.errMsg.append( 'non existent key for pathMap2 '+ what+'<br/>')
                    path = self.pathMap2[what].replace('REL', self.build)

                    logFileName = "not_found"
                    try:  # log files may not exist yet ...
                        index = self.pathMap2[what]+sample.replace(' PILEUP','_PU')+'_Memcheck'
                        logFileName = self.allLogs[ index ]
                    except:
                        self.errMsg.append( "log not found for "+index+'<br>')
                        pass

                    if logFileName == 'not_found':
                        cell += '<br /> <em>logfile not yet available</em>'
                    else:
                        cell += '<br /> <b>some error occured, please check the '
                        logName = os.getcwd()+'/'+logFileName
                        if not os.path.exists(logName):
                            # log1 = logName.replace('1of2', '2of2')
                            log2 = logName.replace('2of2', '1of2')
                            # if os.path.exists(log1) : logName = log1
                            if os.path.exists(log2) : logName = log2

                        eCmd = getCmdErr(os.path.dirname(logName), sample)
                        cell += '<a href="'+self.baseURL + logName.replace('/data/intBld','')+'">'
                        cell += 'logfile </a></b>'
                        cell += '<br /><em>command tried:</em> <br /> <code> '+eCmd+' </code>'
                    
                row.append(cell)
            self.fmtr.writeRow(row)
                    
        self.fmtr.endTable()

    # --------------------------------------------------------------------------------
    
    def analyze(self, summOnly):
    
        self.readXMLFiles()
        
        if summOnly:
            self.fmtr.write("total errors: "+str(self.totErr) )
            return
        
        self.getCommands()

        # now assemble and output the results
        self.fmtr.write("<p>If a field is completely empty, it usually means that the original xml output from valgrind was cut (e.g. by an exception thrown).</p>")
        
        samples = ['TTbar', 'TTbar PILEUP']
        stepMap   = {'GEN-DIGI2RAW' : 'GEN,SIM,DIGI,L1,DIGI2RAW',
                     'FASTSIM' : "FASTSIM",
                     'RAW2DIGI-RECO' : "RAW2DIGI,RECO",
                     'HLT' : "HLT"}
        steps = stepMap.keys()
        steps.sort()
        try:
            self.writeTable(samples, steps)
        except AttributeError:
            self.fmtr.write('<h3>No valgrind results available yet.</h3>')
            return
        
        # for the real data valgrinds ... 
        if self.haveRealData:
            self.fmtr.write('<h3>Real data</h3>')
            samples = ['run2010A']
            stepMap   = { 'RAW2DIGI-RECO' : "RAW2DIGI,RECO",
	                  'RAW2DIGI-RECO-DQM' : "RAW2DIGI,RECO,DQM",
	                }
            steps = stepMap.keys()
            steps.sort()
            self.writeTable(samples, steps)

        if len(self.errMsg)>0:
            self.fmtr.write("<p></p><h4>Summary of errors duing processing:</h4>")
            for m in self.errMsg:
                self.fmtr.write(m+'<br/>')

def main():
    
    form = cgi.FieldStorage()
    
    ## cgi.print_form(form)
    txtOnly  = form.has_key('txt')
    summOnly = form.has_key('summaryOnly')

    style = """
<link rel="stylesheet" type="text/css" href="%s/html/valgrind.css">
""" % (config.siteInfo['macms01Path'].replace('cgi-bin',''))

    fmtr = SimpleHTMLFormatter(title='Valgrind report', style=style)
    
    build = "CMSSW_3_5_X_2009-12-17-1700"
    if form.has_key('ib') :
    	build = form['ib'].value
	# only list the builds with the "canonical" naming structure ... 
    buildRe = re.compile('^CMSSW_\d+_\d+(_.+|)_X_\d\d\d\d-\d\d-\d\d-\d\d\d\d$')
    if not buildRe.match(build):
        fmtr.write("ERROR request for illegal value for build :"+build)
        return
	    
    plat = 'slc5_ia32_gcc434'
    if form.has_key('arch') :
        plat = form['arch'].value
    # only list the builds with the "canonical" naming structure ... 
    archRe = re.compile('^(slc|osx)\d*_(ia|amd)\d\d_gcc\d\d\d$')
    if not archRe.match(plat):
        fmtr.write("ERROR request for illegal value for arch :"+plat)
        return

    vgr = VGResults(plat, build, fmtr)
    vgr.analyze(summOnly)

if __name__ == '__main__':
	main()

