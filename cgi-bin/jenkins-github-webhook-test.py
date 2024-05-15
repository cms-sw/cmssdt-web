#!/usr/bin/env python
from __future__ import print_function
from jenkins_callback import build_jobs
import sys, json

try: jenkins_server=sys.argv[1]
except: jenkins_server="http://cmsjenkins01.cern.ch:8080/jenkins"

params = []
params.append({"name":"JOB_PARAM1","value":"cmssdt1"})
params.append({"name":"JOB_PARAM2","value":"cmssdt2"})

build_jobs(jenkins_server, [(json.dumps({"parameter":params}),"jenkins-installation-trigger-cli")])
