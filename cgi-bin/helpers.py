
import re, os
# --------------------------------------------------------------------------------
archList = []

activeReleaseCycles = [ '7.6', '7.5', '7.4', '7.1', '7.0', '6.2', '5.3' ]
# --------------------------------------------------------------------------------

def defaultPlat(release):
    verExp = re.compile(r'^CMSSW_(\d+)_(\d+).+')
    arch = 'slc5_amd64_gcc434'
    m =  verExp.match(release)
    if m:
       relSer = int(m.group(1))
       if relSer > 4: arch = 'slc5_amd64_gcc462'
    return arch

# --------------------------------------------------------------------------------

def isValidPlat(plat):
    if re.match('^[^_]+_[^_]+_[^_]+$',plat): return True
    return False

# --------------------------------------------------------------------------------

def isValidRelease(vers):
    validVersRe = re.compile(r'^CMSSW_\d+_\d+(_[\w\d]+|)_X(_SLHC|)_\d\d\d\d-\d\d-\d\d-\d\d\d\d$')
    return validVersRe.match(vers)

# --------------------------------------------------------------------------------

def getReleaseSeries(ver):
    ser,ex = re.search(r'^(CMSSW_\d+_\d+(_[\w\d]+|)_X)(_SLHC|)_\d\d\d\d-\d\d-\d\d-\d\d\d\d$',ver).groups()
    return ser

# --------------------------------------------------------------------------------

def getValgrindErrors(ib, arch):
    return -1
    import config

    import urllib2
    vgUrl = config.siteInfo['macms01Path']+'showValgrindResults.py?ib=%s&arch=%s&summaryOnly=1'

    page = urllib2.urlopen(vgUrl % (ib, arch))
    content = page.readlines()
    nErr = -1
    for line in content:
        if 'Error no info available for' in line:
            nErr = -1
            return str(nErr)
        if 'total errors' in line:
            nErr = line.split(':')[-1].strip()

    return str(nErr)

# --------------------------------------------------------------------------------

def getStamp(ib):
    import re, datetime

    wkdy = ['mon','tue','wed','thu','fri','sat','sun']
    cand, date = re.search(r'(\w+)_(\d{4}-\d{2}-\d{2}-\d{4})', ib).groups()
    y,m,d,h = date.split('-')
    weekday = datetime.date(int(y), int(m), int(d)).weekday()
    stamp = wkdy[weekday] +'-' + str(h)[:2]

    cycRe = re.compile('CMSSW_((\d+_\d+)(_.+|))_X')
    cycMatch = cycRe.match(cand)
    if cycMatch:
        cycle = cycMatch.group(1).replace('_','.')
    else:
        cycle = "Unknown"
    
    return wkdy[weekday], stamp, cycle


# --------------------------------------------------------------------------------

def getWallClockTimes(ib, arch=None):

    errLines = []
    stdArch = defaultPlat(ib)
    day, stamp, cycle = getStamp(ib)
    import config
    import glob
    afsPath = os.path.join(config.siteInfo['afsPath'], stdArch, day, cycle + '-' + stamp, ib, 'qaLogs')
    if not os.path.exists (afsPath): afsPath = os.path.join(config.siteInfo['afsPath'], arch, day, cycle + '-' + stamp, ib, 'qaLogs')

    lines = []
    for log in glob.glob(afsPath+'/perfNew-*of*.log'):
        resFile = open(log, 'r')
        lines += resFile.readlines()
        resFile.close()

    # PSR: result for    GEN-DIGI2RAW_cpu6 : 0, time to process: 03:33:44
    # PSR: result for             HLT_cpu4 : 0, time to process: 02:44:20
    wallClockTimes = {}
    for line in lines:
        if not line.startswith('PSR: result for') : continue
        items = line.split()
        try:
            wallClockTimes [items[3].replace('_','/')] = items[-1]
        except:
            errLines.append('error converting/filling'+items)
            print ("ERROR converting/filling: ", items)
            pass
        
    return wallClockTimes, errLines

