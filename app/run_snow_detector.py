import sys
import os.path as op
import json
from s2snow import snow_detector

VERSION="0.1"

def show_help():
    """Show help of the s2snow script"""
    print "This script is used to compute snow mask using OTB applications on Spot/LandSat/Sentinel-2 products from theia platform"
    print "Usage: s2snow.py param.json"
    print "s2snow.py version to show version"
    print "s2snow.py help to show help"

def show_version():
    print VERSION

#----------------- MAIN ---------------------------------------------------

def main(argv):
    """ main script of snow extraction procedure"""

    json_file=argv[1]

    #load json_file from json files
    with open(json_file) as json_data_file:
      data = json.load(json_data_file)
    pout = data["general"]["pout"]
    sys.stdout = open(op.join(pout, "stdout.log"), 'w')
    sys.stderr = open(op.join(pout, "stderr.log"), 'w')
    sd = snow_detector.snow_detector(data)
      
    sd.detect_snow(2)
      
if __name__ == "__main__":
    if len(sys.argv) != 2 :
        show_help()
    else:
        if sys.argv[1] == "version":
            show_version()
        elif sys.argv[1] == "help":
            show_help()
        else:
            main(sys.argv)
