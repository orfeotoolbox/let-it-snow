#!/usr/bin/env python

import sys
import os.path as op
import json
from s2snow import snow_detector

VERSION = "1.2"


def show_help():
    """Show help of the run_snow_detector script"""
    print "This script is used to run the snow detector module that compute snow mask using OTB applications on Spot/LandSat/Sentinel-2 products from theia platform"
    print "Usage: python run_snow_detector.py param.json"
    print "python run_snow_detector.py version to show version"
    print "python run_snow_detector.py help to show help"


def show_version():
    print VERSION

# ----------------- MAIN ---------------------------------------------------


def main(argv):
    """ main script of snow extraction procedure"""

    json_file = argv[1]

    # Load json_file from json files
    with open(json_file) as json_data_file:
        data = json.load(json_data_file)

    general = data["general"]
    pout = general.get("pout")
    log = general.get("log", True)

    if log:
        sys.stdout = open(op.join(pout, "stdout.log"), 'w')
        sys.stderr = open(op.join(pout, "stderr.log"), 'w')

    sd = snow_detector.snow_detector(data)
    sd.detect_snow(2)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        show_help()
    else:
        if sys.argv[1] == "version":
            show_version()
        elif sys.argv[1] == "help":
            show_help()
        else:
            main(sys.argv)
