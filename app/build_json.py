#!/usr/bin/env python

import sys
import os.path as op
import json
import argparse

def show_help():
    """Show help of the build_json script for theia N2A products"""
    print "This script is used to build json configuration file use then to compute snow mask using OTB applications on Spot/LandSat/Sentinel-2 products from theia platform"
    print "Usage: python build_theia_json -s [landsat|s2|take5] -d image_directory -e srtm_tile -o file.json"
    print "python run_snow_detector.py help to show help"


#----------------- MAIN ---------------------------------------------------

def main():
    """ Script to build json from theia N2A product"""

    parser = argparse.ArgumentParser(description='Build json from THEIA product')

    parser.add_argument("-s", help="select input sensors")
    parser.add_argument("-d", help="input dir")
    parser.add_argument("-o", help="input dir")
    parser.add_argument("-do", help="input dir")

    args = parser.parse_args()
    
    #print(args.accumulate(args.integers))

    #Parse sensor
    if (args.s == 's2'):
        multi=10
    #Build json file
    data = {}

    data["general"]={
        "pout":args.do,
        "nodata":-10000,
        "ram":1024,
	"nb_threads":1,
	"generate_vector":"false",
	"preprocessing":"false",
	"log":"true",
	"multi":10
    }

    data["cloud"]={
        "shadow_mask":32,
        "all_cloud_mask":1,
        "high_cloud_mask":128,
        "rf":12,
        "red_darkcloud":500,
        "red_backtocloud":100
    }
    data["snow"]={
        "dz":100,
        "ndsi_pass1":0.4,
        "red_pass1":200,
        "ndsi_pass2":0.15,
        "red_pass2":120,
        "fsnow_lim":0.1,
        "fsnow_total_lim":0.001
    }
    
    fp = open(args.o, 'w')
    fp.write(json.dumps(data,indent=4, sort_keys=True))
    fp.close()
      
if __name__ == "__main__":
    main()
