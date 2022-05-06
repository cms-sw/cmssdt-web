#!/usr/bin/env python

import os, sys

import json 

from pickle import Pickler

def json2pkl(inFile, outFile=None):

    if not outFile:
        outFile = inFile.replace('.json', '.pkl')

    jF = open(inFile, 'r')
    data = json.load(jF)
    jF.close()

    pF = open(outFile, 'wb')
    pklr = Pickler(pF, protocol=2)
    pklr.dump(data)
    	    	    
    pF.close()

    print "Successfully converted ",inFile, ' to ', outFile

#     aaData = []
#     ib = data[0]
#     for i,s in data[1].items():
#         try:
#             aaData.append([ib, 'dirSize', i, s])
#         except Exception, e:
#             print "ERROR for dir ", item
#             raise e
#     for i,s in data[2].items():
#         try:
#             aaData.append([ib, 'fileSize', i, s])
#         except Exception, e:
#             print "ERROR for file ", item
#             raise e
# 
#     jfo = open('../html/treeInfo-IBsrc.json', 'w')
#     json.dump({ 'aaData' : aaData }, jfo)
#     jfo.close()

    return
if __name__ == '__main__':

    inFile = sys.argv[1]
    outFile = None
    if len(sys.argv) > 2:
        outFile = sys.argv[2]
        
    json2pkl(inFile, outFile)
