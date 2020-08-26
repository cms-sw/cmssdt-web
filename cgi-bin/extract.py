#!/usr/bin/env python

import zipfile
import os

if __name__ == "__main__":
	print "Content-Type: text/html\n"
	print 'from the script', os.environ['REQUEST_URI'], '</br>
	print 'Hello'

