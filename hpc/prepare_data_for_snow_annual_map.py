#!/usr/bin/env python
# -*- coding: utf-8 -*-
#=========================================================================
#
#  Program:   lis
#  Language:  Python
#
#  Copyright (c) Germain Salgues
#  Copyright (c) Manuel Grizonnet
#
#  See lis-copyright.txt for details.
#
#  This software is distributed WITHOUT ANY WARRANTY; without even
#  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.  See the above copyright notices for more information.
#
#  this file requires python/3.5.2 and amalthee/0.1
#=========================================================================
import os
import sys
import os.path as op
import json
import csv
import logging
import subprocess
from datetime import datetime, timedelta
from libamalthee import Amalthee

def str_to_datetime(date_string, format="%Y%m%d"):
    """ Return the datetime corresponding to the input string
    """
    logging.debug(date_string)
    return datetime.strptime(date_string, format)

def datetime_to_str(date, format="%Y%m%d"):
    """ Return the datetime corresponding to the input string
    """
    logging.debug(date)
    return date.strftime(format)
    
def call_subprocess(process_list):
    """ Run subprocess and write to stdout and stderr
    """
    logging.info("Running: " + " ".join(process_list))
    process = subprocess.Popen(
        process_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = process.communicate()
    logging.info(out)
    sys.stderr.write(err)

class prepare_data_for_snow_annual_map():
    def __init__(self, params):
        logging.info("Init snow_multitemp")
        self.raw_params = params

        self.tile_id = params.get("tile_id")
        self.date_start = str_to_datetime(params.get("date_start"), "%d/%m/%Y")
        self.date_stop = str_to_datetime(params.get("date_stop"), "%d/%m/%Y")
        self.date_margin = timedelta(days=params.get("date_margin", 0))
        self.output_dates_filename = params.get("output_dates_filename", None)
        self.mode = params.get("mode", "RUNTIME")

        self.input_dir = str(params.get("input_dir"))
        self.path_tmp = str(params.get("path_tmp", os.environ.get('TMPDIR')))

        self.path_out = op.join(str(params.get("path_out")),
                                self.tile_id + "_" + datetime_to_str(self.date_start)
                                + "-" + datetime_to_str(self.date_stop))

        if not os.path.exists(self.path_out):
            os.mkdir(self.path_out)

        self.ram = params.get("ram", 512)
        self.nbThreads = params.get("nbThreads", None)

        self.snow_products_availability = 0
        self.datalake_products_availability = 0

    def run(self):
        logging.info('Process tile:' + self.tile_id + '...')
        
        search_start_date = self.date_start - self.date_margin
        search_stop_date = self.date_stop + self.date_margin
        
        parameters = {"processingLevel": "LEVEL2A", "location":str(self.tile_id)}
        amalthee_theia = Amalthee('theia')
        amalthee_theia.search("SENTINEL2",
                              datetime_to_str(search_start_date, "%Y-%m-%d"),
                              datetime_to_str(search_stop_date, "%Y-%m-%d"),
                              parameters,
                              nthreads = self.nbThreads)

        nb_products = amalthee_theia.products.shape[0]
        logging.info('There is ' + str(nb_products) + ' products for the current request')

        df = amalthee_theia.products
        df['snow_product'] = ""
        df['snow_product_available'] = False
        snow_product_available = 0
        datalake_product_available = 0
        datalake_update_requested = 0
        
        for product_id in df.index:
            logging.info('Processing ' + product_id)

            # check datalake availability
            if df.loc[product_id, 'available']:
                datalake_product_available += 1

            # check snow product availability
            expected_snow_product_path = op.join(self.input_dir, self.tile_id, product_id)
            df.loc[product_id, 'snow_product'] = expected_snow_product_path
            logging.info(expected_snow_product_path)

            if op.exists(expected_snow_product_path):
                logging.info(product_id + " is available as snow product")
                snow_product_available += 1
                df.loc[product_id, 'snow_product_available'] = True
            elif df.loc[product_id, 'available']:
                logging.info(product_id + " requires to generate the snow product")
                self.process_snow_product(product_id)
            else:
                logging.info(product_id + " requires to be requested to datalake.")
                datalake_update_requested += 1

        self.snow_products_availability = float(snow_product_available/nb_products)
        logging.info("Percent of available snow product : " + str(100*self.snow_products_availability) + "%")
        
        self.datalake_products_availability = float(datalake_product_available/nb_products)
        logging.info("Percent of available datalake product : " + str(100*self.datalake_products_availability) + "%")
        
        # TODO add datalake update if not all the products are available
        if datalake_update_requested > 0:
            logging.info("Requesting an update of the datalake because of " + datalake_update_requested + " unavailable products...")
            #amalthee_theia.fill_datalake()
            logging.info("End of requesting datalake.")            

        # Create fill to access requested products status
        products_file = op.join(self.path_out, "input_datalist.csv")
        logging.info("Products detailed status is avaible under: " + products_file)
        df.to_csv(products_file, sep=';')

    def build_json(self):
        if self.snow_products_availability > 0.9:
            snow_annual_map_param_json = os.path.join(self.path_out, "param.json")
            logging.info("Snow annual map can be computed from: " + snow_annual_map_param_json)
            self.raw_params['data_availability_check'] = True
            self.raw_params['log'] = True
            self.raw_params['log_stdout'] = op.join(self.path_out,"stdout.log")
            self.raw_params['log_stderr'] = op.join(self.path_out,"stderr.log")
            jsonFile = open(snow_annual_map_param_json, "w")
            jsonFile.write(json.dumps(self.raw_params, indent=4))
            jsonFile.close()
        else:
            logging.error("Snow annual map cannot be computed because of too many missing products")

    def process_snow_product(self, product_id):
        logging.info("Ordering processing of the snow product for " + product_id)
        command = ["qsub",
                   "-v",
                   "tile="+self.tile_id[1:]+",outpath="+self.input_dir,
                   "runTile_lis_Sentinel2_datalake_anytile.sh"]
        #call_subprocess(command)
        logging.info("Order was submitted the snow product will soon be available.")

def main():
    params = {"tile_id":"T32TPS",
              "date_start":"01/09/2017",
              "date_stop":"31/08/2018",
              "date_margin":15,
              "mode":"DEBUG",
              "input_dir":"/work/OT/siaa/Theia/Neige/PRODUITS_NEIGE_LIS_develop_1.5",
              "path_tmp":"",
              "path_out":"/work/OT/siaa/Theia/Neige/Snow_Annual_Maps",
              "ram":2048,
              "nbThreads":5,
              "use_l8_for_densification":False,
              "data_availability_check":False}

    with open('selectNeigeSyntheseMultitemp.csv', 'r') as csvfile:
        tilesreader = csv.reader(csvfile)
        firstline = True
        for row in tilesreader:
            if firstline:    #skip first line
                firstline = False
            else:
                tile_id = 'T' + str(row[0])
                params['tile_id'] = tile_id

                prepare_data_for_snow_annual_map_app = prepare_data_for_snow_annual_map(params)
                prepare_data_for_snow_annual_map_app.run()
                prepare_data_for_snow_annual_map_app.build_json()


if __name__== "__main__":
    # Set logging level and format.
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=\
        '%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s')
    main()


