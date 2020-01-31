#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path as op
import json
from s2snow import cloud_removal

VERSION="0.1"

def show_help():
    """Show help of the run_cloud_removal script"""
    print("Usage: python run_cloud_removal.py param.json")
    print("python run_cloud_removal.py version to show version")
    print("python run_cloud_removal.py help to show help")

def show_version():
    print(VERSION)

#----------------- MAIN ---------------------------------------------------

def main(argv):
    """ main script of snow extraction procedure"""

    json_file=argv[1]

    #load json_file from json files
    with open(json_file) as json_data_file:
      data = json.load(json_data_file)
    
    general = data["general"]
    pout = general.get("pout")
    
    log = general.get("log", True)
    if log:
        sys.stdout = open(op.join(pout, "stdout.log"), 'w')
        sys.stderr = open(op.join(pout, "stderr.log"), 'w')
    
    cloud_removal.run(data)
      
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
