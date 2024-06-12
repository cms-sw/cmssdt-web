#!/usr/bin/env python3

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

    print ("Successfully converted ",inFile, ' to ', outFile)

    return
if __name__ == '__main__':

    inFile = sys.argv[1]
    outFile = None
    if len(sys.argv) > 2:
        outFile = sys.argv[2]
        
    json2pkl(inFile, outFile)
