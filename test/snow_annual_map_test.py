#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import os.path as op
import logging

from s2snow import snow_annual_map_evaluation

def main(argv):
    logging.info("Start snow_annual_map_test")

    data_path = str(argv[1])
    out_path = str(argv[2])
    if not op.exists(out_path):
        os.mkdir(out_path)
    tmp_path = str(argv[3])
    if not op.exists(tmp_path):
        os.mkdir(tmp_path)

    # Remove the target file, because the success of the test depends on this file creation
    target_file = op.join(out_path, "T31TCH_20180101_20180131", "SNOW_OCCURENCE_T31TCH_20180101_20180131.tif")
    if op.exists(target_file):
        os.remove(target_file)

    params = {
            "densification_products_list": [
                op.join(data_path,"LANDSAT8-OLITIRS-XS_20180115-103629-617_L2A_T31TCH_D_V1-9"),
                op.join(data_path,"LANDSAT8-OLITIRS-XS_20180131-103619-890_L2A_T31TCH_D_V1-9")
            ],
            "date_margin": 10,
            "path_out": out_path,
            "mode": "DEBUG",
            "input_products_list": [
                op.join(data_path,"SENTINEL2A_20180101-105435-457_L2A_T31TCH_D_V1-4"),
                op.join(data_path,"SENTINEL2A_20180131-105416-437_L2A_T31TCH_D_V1-4")
            ],
            "log": True,
            "date_start": "01/01/2018",
            "path_tmp": tmp_path,
            "ram": 1024,
            "use_densification": True,
            "data_availability_check": True,
            "tile_id": "T31TCH",
            "date_stop": "31/01/2018",
            "nbThreads": 1}

    # Run the snow detector
    snow_annual_map_evaluation_app = snow_annual_map_evaluation.snow_annual_map_evaluation(params)
    snow_annual_map_evaluation_app.run()

    if params.get("run_comparison_evaluation", False):
        snow_annual_map_evaluation_app.run_evaluation()

    if params.get("run_modis_comparison", False):
        snow_annual_map_evaluation_app.compare_modis()

    if not op.exists(op.join(out_path, "T31TCH_20180101_20180131", "SNOW_OCCURENCE_T31TCH_20180101_20180131.tif")):
        logging.error("The target does not exists, the test has failed")
        sys.exit(1)
    logging.info("End snow_annual_map_test")

if __name__== "__main__":
    # Set logging level and format.
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=\
        '%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s')
    main(sys.argv)
