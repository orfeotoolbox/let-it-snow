#!/usr/bin/python
#coding=utf8
#=========================================================================
#
#  Program:   lis
#  Language:  Python
#
#  Copyright (c) Simon Gascoin
#  Copyright (c) Manuel Grizonnet
#
#  See lis-copyright.txt for details.
#
#  This software is distributed WITHOUT ANY WARRANTY; without even
#  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.  See the above copyright notices for more information.
#
#=========================================================================

import numpy as np
from matplotlib import pyplot as plt
from optparse import OptionParser

def load_histo(histo_path):
        with open(histo_path) as f:
  		v = np.loadtxt(f, delimiter=",", dtype='float', comments="#", skiprows=3, usecols=(0,3,4))

        fsnow_rate=v[:,1]/(v[:,1]+v[:,2])

        #print v[:,1]
        #print v[:,2]
        #b = np.zeros(6).reshape(2, 3)
        
        #print fsnow_rate
        print fsnow_rate[0]
        print fsnow_rate
        print np.shape(fsnow_rate)[0]
        plt.plot(np.arange(np.shape(fsnow_rate)[0]), fsnow_rate[:], 'ro')
        #plt.axis([0, 6, 0, 20])
        plt.show()

def print_histo(histo_path):
	with open(histo_path) as f:
  		v = np.loadtxt(f, delimiter=",", dtype='int', comments="#", skiprows=3, usecols=(0,1,3))

	#_hist = np.ravel(v)   # 'flatten' v
	#fig = plt.figure()
	#ax1 = fig.add_subplot(111)

	#n, bins, patches = ax1.hist(v_hist, bins=50, normed=1, facecolor='green')
	#plt.show()

	print v

	dem=v[:,0]
	width = 0.8
	#indices = np.arange(len(dem))

	plt.bar(dem, v[:,1], width=width, color="red", label="all")
	plt.bar([i+0.25*width for i in dem], v[:,2], width=0.5*width, color="blue", alpha=1. , label="snow")

	plt.xticks(dem+width/2., 
           [i for i in dem] )

	plt.legend()	
	plt.show()

def main():
    parser = OptionParser(usage="usage: %prog [options] filename",
                          version="%prog")

    parser.add_option("-f","--file", help="absolute path to histogram file", dest="histo_path", type="string")
    #parser.add_option("-f","--file", help="absolute path to histogram file", dest="histo_path", type="string")

    (opts, args) = parser.parse_args()

    if opts.histo_path is None: 
        print "A mandatory option is missing\n"
        parser.print_help()
        exit(-1)
    else:
        #print opts.path
        #print_histo(opts.histo_path)
        load_histo(opts.histo_path)   
if __name__ == '__main__':
    main()
   
