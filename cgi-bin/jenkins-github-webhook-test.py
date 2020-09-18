#!/usr/bin/env python
import sys, json
import urllib2, urllib, cookielib

try: jenkins_server=sys.argv[1]
except: jenkins_server="http://cmsjenkins03.cern.ch:8080/jenkins"
try: login_key=sys.argv[2]
except: login_key='ADFS_LOGIN'

params = []
job="jenkins-installation-trigger-cli"
params.append({"name":"JOB_PARAM1","value":"cmssdt1"})
params.append({"name":"JOB_PARAM2","value":"cmssdt2"})
url = jenkins_server+'/job/'+job+'/build'
jenkins_parameters = json.dumps({"parameter":params})
print jenkins_parameters,job
data = {
  "json": jenkins_parameters,
   "Submit": "Build"
}

cookie_jar = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
urllib2.install_opener(opener)
headers = {login_key : "cmssdt"}
try:
  req = urllib2.Request(url=jenkins_server+'/crumbIssuer/api/json', headers=headers)
  crumb = json.loads(urllib2.urlopen(req).read())
  headers[crumb['crumbRequestField']] = crumb['crumb']
  print "OK crumbRequest"
except urllib2.HTTPError as e:
  print "Running without Crumb Issuer:",e
  pass

try:
  data=urllib.urlencode(data)
  req = urllib2.Request(url=url,data=data,headers=headers)
  content = urllib2.urlopen(req).read()
except Exception as e:
  print "Unable to start jenkins job:", e

