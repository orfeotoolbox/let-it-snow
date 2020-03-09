#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os.path as op
import json
import logging
from s2snow import snow_annual_map_evaluation

VERSION = "0.1.0"


def show_help():
    """Show help of the run_snow_annual_map script"""
    print("This script is used to run the snow annual map " \
          + "module that compute snow coverage onto a given date range")
    print("Usage: python run_snow_annual_map.py param.json")
    print("python run_snow_annual_map.py version to show version")
    print("python run_snow_annual_map.py help to show help")


def show_version():
    print(VERSION)

# ----------------- MAIN ---------------------------------------------------


def main(argv):
    """ main script of snow extraction procedure"""

    json_file = argv[1]

    # Load json_file from json files
    with open(json_file) as json_data_file:
        data = json.load(json_data_file)

    pout = data.get("path_out")
    log = data.get("log", True)

    if log:
        sys.stdout = open(data.get('log_stdout', op.join(pout, "stdout.log")), 'w')
        sys.stderr = open(data.get('log_stderr', op.join(pout, "stderr.log")), 'w')

    # Set logging level and format.
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, \
        format='%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s')
    logging.info("Start run_snow_annual_map.py")
    logging.info("Input args = " + json_file)

    # Run the snow detector
    snow_annual_map_evaluation_app = snow_annual_map_evaluation.snow_annual_map_evaluation(data)
    snow_annual_map_evaluation_app.run()

    if data.get("run_comparison_evaluation", False):
        snow_annual_map_evaluation_app.run_evaluation()

    if data.get("run_modis_comparison", False):
        snow_annual_map_evaluation_app.compare_modis()

    logging.info("End run_snow_annual_map.py")

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
