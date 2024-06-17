#!/usr/bin/env python3

import re, os

import config

class mkDepMetrics(object) :
    def __init__(self, page, arch, packagename, relPath) :
        self.page=page
        self.arch = arch
        self.packagename = packagename
        cmd = 'true'
        metrics = relPath+'/igRun/metrics'
        if os.path.exists(metrics): cmd = 'cat '+metrics
        if not cmd:
            url = config.siteInfo['macms01Path']+'/ignominy/'+arch+'/'+packagename+'/igRun/metrics'
            url = url.replace('cgi-bin', 'html/incoming')
            cmd = 'wget --no-check-certificate -nv -o /dev/null -O- '+url
	
        temp = os.popen(cmd)
        self.contents = temp.readlines()

        self.summary = ''
        self.cycles  = ''
        self.levels  = ''
        self.infoMsg = '''<pre> <font size="-2">
        * CCD:  Cumulative Component Dependency measures the cumulative testing cost
            across the system.
        * ACD:  Average Component Dependency indicates the number of other packages
            an average package depends on.
        * NCCD: Normalised Cumulative Component Dependency measures how the structure
            differs from a balanced binary tree of comparable size. If NCCD is one,
            the structure resembles a binary tree; if much less than one, the
            packages are mostly independent; if much greater than one, the system
            is fairly strongly coupled. The only universal NCCD target is to
            minimise for any given software system--a high value indicates a
            strongly coupled system and less coupling is better.
        </font></pre>
        '''

    def makeSummary(self):
        contents=self.contents
        writeflag = False
        cycleflag = False
        typeCycle = re.compile('^(Cycle \w*)')
        if len(contents)==0 :
            # self.page.write('<ul><li> No data about summary\n</li></ul>')
            return False
        for line in contents :
            matchCycle = typeCycle.search(line)
            if line=='# Summary\n' :
                self.summary += '<table borders="0" cellpadding="0" cellspacing="0">'
                self.summary += '<tr><td>\n'
                self.summary += '<ul><li> Summary <ul>\n'
                writeflag = True
            elif line=='# Levels\n' :
                writeflag = False
                cycleflag = False
                self.levels += '</ul> </span> </a> </div>'
                # self.levels += ' </ul> '
                break
            elif line=='\n' :
                continue
            elif line[0:5] =='* CCD' :
                writeflag = False
            elif line=='# Cycles\n' :
                self.cycles += '</ul></ul>\n'
                self.cycles += '</td><td>'
                self.cycles += '<div> <a class="detail" name="explain" onclick="showHide(this) "> explain CCD ACD and NCCD </a> </div>'
                self.cycles += '<div> <a class="info"   name="explain" onclick="showHide(this) "> '+self.infoMsg+'</a></div>'
                self.cycles += '</td></tr></table>'

                self.cycles += '\n<div> <a class="detail" name="cycles" onclick="showHide(this) "> show details for cycles </a> '
                self.cycles += '\n<div> <a class="info"   name="cycles" onclick="showHide(this) "> hide details for cycles <span> '
                self.cycles += '\n<ul class="infoList"> <li> Cycles</li>\n'
                cycleflag=True
            elif matchCycle and cycleflag and matchCycle.group(1)=='Cycle 1':
                self.cycles += '<ul><li> '+matchCycle.group(1)+'</li>\n<ul>\n'
            elif matchCycle and cycleflag :
                self.cycles += '</ul></ul>\n<ul><li> '+matchCycle.group(1)+'</li>\n<ul>\n'
            elif cycleflag :
                self.cycles += '<li> '+line.strip()+'</li>\n'
            elif writeflag :
                self.summary += '<li> '+line+'</li>\n'
            else :
                continue

    def packlist(self):
        contents=self.contents   
        pack = [['Levels']]
        j=0
        writeflag = False
        valueflag = False
        if len(contents)==0 : 
            # self.page.write('<ul><li> No data about metrics information.</li></ul>\n')
            return pack
        for line in contents :
            if line =='# Levels\n' :
                writeflag = True
                continue
            elif not writeflag :
                continue
            if line=='\n':
                continue
            matchLevel = re.search('[0-9]. ',line)
            if matchLevel :
                j = j + 1
                temp = line.split()
                pack.append(temp)
                valueflag=True
                continue
            if valueflag :
                if line=='\n' :
                    valueflag=False
                    continue
                else :
                    temp =line.strip()
                    pack[j].append(temp)
        return pack
# repack return list [[levels], [level1, [PACKEGE1,module1,module2,...], [PACKEGE2,module1,module2], ..],[level2,[],[],...] ...]
    def repack(self,pack):
        listlen = len(pack)
        pack2 = [['Levels']]
        countpack = 0
        for i in range(1,listlen):
            packname = [[str(i)]]
            check = 1
            for j in range(1,len(pack[i])):

                m = re.search('/',pack[i][j])
                per = m.span()
                title = pack[i][j][0:per[0]]
                module = pack[i][j][per[1]:]
                if j==1:
                    temp = []
                    temp.append(title)
                    packname.append(temp)
                    packname[check].append(module)
                else:
                    if packname[check][0]==title:
                        packname[check].append(module)
                    else:
                        check = check + 1
                        temp = []
                        temp.append(title)
                        packname.append(temp)
                        packname[check].append(module)

            pack2.append(packname)
        return pack2 

    def dropdown(self,list):
        self.levels += '\n<div> <a class="detail" name="levels" onclick="showHide(this) "> show details for levels </a> \n'
        self.levels += '\n<div> <a class="info"   name="levels" onclick="showHide(this) "> hide details for levels <br /> </a>\n <span>'
        self.levels += '\n<div class="menu">\n\n'
        listlen = len(list)
        for level in range(1,listlen):
            self.levels += '<ul>\n<li><a href="#"> Level '+str(list[level][0][0])+'<!--[if IE 7><!--></a><!--<![endif]-->\n<!--[if lte IE 6]><table><tr><td><![endif]-->\n<ul>\n\n'
            for pack in range(1,len(list[level])):
                self.levels += '<li><a class="drop" href="#"> '+str(list[level][pack][0])+'<!--[if IE 7><!--></a><!--<![endif]-->\n<!--[if lte IE 6]><table><tr><td><![endif]-->\n<ul>\n'
                for module in range(1,len(list[level][pack])):
                    self.levels += '<li> <a href=\"'+config.siteInfo['macms01Path']+'/ignominy/'+self.arch+'/'+self.packagename+'/igRun/subsystem.'+str(list[level][pack][0])+'/PROJECT-'+str(list[level][pack][0])+'-'+str(list[level][pack][module].replace('/','-'))+'-O.gif.html\">'+str(list[level][pack][module])+'</a></li>\n'
                self.levels += '</ul>\n'
            self.levels += '</li></ul></li></ul>\n'
        if listlen > 0: 
            self.levels += '</div><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>\n'
        else:
            self.leves += '</div><br><br><br>\n'
        self.levels += ' </span> </div> '



if __name__=="__main__" :
    from makeDepMetrics import mkDepMetrics
    file = open("sample.html",'w')
    mkDM= mkDepMetrics(file, 'slc5_amd64_gcc434','CMSSW_4_2_X_2011-01-28-1300')
    summary = mkDM.makeSummary()
    print (summary)
    pkglist = mkDM.packlist()
    outputlist = mkDM.repack(pkglist)
    mkDM.dropdown(outputlist)

