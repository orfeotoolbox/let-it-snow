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
import copy
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
    sys.stderr.write(str(err))

class prepare_data_for_snow_annual_map():
    def __init__(self, params):
        logging.info("Init snow_multitemp")
        self.raw_params = copy.deepcopy(params)

        self.tile_id = params.get("tile_id")
        self.date_start = str_to_datetime(params.get("date_start"), "%d/%m/%Y")
        self.date_stop = str_to_datetime(params.get("date_stop"), "%d/%m/%Y")
        self.date_margin = timedelta(days=params.get("date_margin", 0))
        self.output_dates_filename = params.get("output_dates_filename", None)
        self.mode = params.get("mode", "RUNTIME")
        self.mission_tags = ["SENTINEL2"]#["LANDSAT"]#

        self.snow_products_dir = str(params.get("snow_products_dir"))
        self.path_tmp = str(params.get("path_tmp", os.environ.get('TMPDIR')))

        self.input_products_list=params.get("input_products_list",[]).copy()
        logging.info(self.input_products_list)
        self.processing_id = self.tile_id + "_" + \
                             datetime_to_str(self.date_start) + "_" + \
                             datetime_to_str(self.date_stop)

        self.path_out = op.join(str(params.get("path_out")), self.processing_id)
        self.use_densification = params.get("use_densification", False)
        if self.use_densification:
            self.mission_tags.append("LANDSAT")
            self.densification_products_list=params.get("densification_products_list",[]).copy()
            logging.info(self.densification_products_list)

        if not os.path.exists(self.path_out):
            os.mkdir(self.path_out)

        self.ram = params.get("ram", 512)
        self.nbThreads = params.get("nbThreads", None)

        self.snow_products_availability = 0
        self.datalake_products_availability = 0

    def run(self):
        logging.info('Process tile:' + self.tile_id +'.')
        logging.info(' for period ' + str(self.date_start) + ' to ' + str(self.date_stop))

        # compute the range of required snow products
        search_start_date = self.date_start - self.date_margin
        search_stop_date = self.date_stop + self.date_margin

        # open a file to store the list of L2A products for which we need to generate the snow products
        filename_i = os.path.abspath(self.processing_id +"_pending_for_snow_processing.txt")
        FileOut = open(os.path.join(".", filename_i),"w")

        resulting_df = None
        snow_processing_requested = 0

        # loop on the different type of products to require
        for mission_tag in self.mission_tags:
            # use amalthee to request the products from Theia catalogues
            parameters = {"processingLevel": "LEVEL2A", "location":str(self.tile_id)}
            amalthee_theia = Amalthee('theia')
            amalthee_theia.search(mission_tag,
                                  datetime_to_str(search_start_date, "%Y-%m-%d"),
                                  datetime_to_str(search_stop_date, "%Y-%m-%d"),
                                  parameters,
                                  nthreads = self.nbThreads)

            nb_products = amalthee_theia.products.shape[0]
            logging.info('There are ' + str(nb_products) + ' ' + mission_tag + ' products for the current request')

            snow_products_list=[]
            if nb_products:
                # get the dataframe containing the requested products and append extra needed fields.
                df = amalthee_theia.products
                df['snow_product'] = ""
                df['snow_product_available'] = False
                snow_product_available = 0
                datalake_product_available = 0
                datalake_update_requested = 0

                # loop on each products from the dataframe
                for product_id in df.index:
                    logging.info('Processing ' + product_id)

                    # check datalake availability
                    if df.loc[product_id, 'available']:
                        datalake_product_available += 1

                    # check snow product availability
                    expected_snow_product_path = op.join(self.snow_products_dir, self.tile_id, product_id)
                    df.loc[product_id, 'snow_product'] = expected_snow_product_path
                    logging.info(expected_snow_product_path)

                    # the snow product is already available
                    if op.exists(expected_snow_product_path):
                        logging.info(product_id + " is available as snow product")
                        snow_product_available += 1
                        df.loc[product_id, 'snow_product_available'] = True
                        snow_products_list.append(expected_snow_product_path)
                    # the L2A product is available in the datalake but request a snow detection
                    elif df.loc[product_id, 'available']:
                        logging.info(product_id + " requires to generate the snow product")
                        snow_processing_requested += 1
                        FileOut.write(df.loc[product_id, 'datalake']+"\n")
                    # the product must be requested into the datalake before snow detection
                    else:
                        logging.info(product_id + " requires to be requested to datalake.")
                        datalake_update_requested += 1

                if resulting_df is not None:
                    resulting_df = resulting_df.append(df)
                else:
                    resulting_df = df

                self.snow_products_availability = float(snow_product_available/nb_products)
                logging.info("Percent of available snow product : " + str(100*self.snow_products_availability) + "%")

                self.datalake_products_availability = float(datalake_product_available/nb_products)
                logging.info("Percent of available datalake product : " + str(100*self.datalake_products_availability) + "%")

                # datalake update if not all the products are available
                if datalake_update_requested > 0:
                    logging.info("Requesting an update of the datalake because of " + str(datalake_update_requested) + " unavailable products...")
                    # this will request all products of the request
                    # @TODO request only the products for which the snow products are not available
                    amalthee_theia.fill_datalake()
                    logging.info("End of requesting datalake.")
            # we only append a single type of products to the main input list
            if mission_tag == "SENTINEL2":#"LANDSAT":#
                self.input_products_list.extend(snow_products_list)
            # the other types are use for densification purpose only
            else:
                self.densification_products_list.extend(snow_products_list)

        # request snow detection processing for listed products
        FileOut.close()
        if snow_processing_requested != 0:
            self.process_snow_products(filename_i, snow_processing_requested)

        # Create fill to access requested products status
        if resulting_df is not None:
            products_file = op.join(self.path_out, "input_datalist.csv")
            logging.info("Products detailed status is avaible under: " + products_file)
            resulting_df.to_csv(products_file, sep=';')
        else:
            logging.error("No products available to compute snow annual map!!")

    def build_json(self):
        # the json is created only is more than 99.9% of the snow products are ready
        # @TODO this param should not be hard coded
        if self.snow_products_availability > 0.999:
            snow_annual_map_param_json = os.path.join(self.path_out, "param.json")
            logging.info("Snow annual map can be computed from: " + snow_annual_map_param_json)
            self.raw_params['data_availability_check'] = True
            self.raw_params['log'] = True
            self.raw_params['log_stdout'] = op.join(self.path_out,"stdout.log")
            self.raw_params['log_stderr'] = op.join(self.path_out,"stderr.log")
            self.raw_params['input_products_list'] = self.input_products_list
            if self.use_densification:
                self.raw_params['densification_products_list'] = self.densification_products_list
            jsonFile = open(snow_annual_map_param_json, "w")
            jsonFile.write(json.dumps(self.raw_params, indent=4))
            jsonFile.close()
            return snow_annual_map_param_json
        else:
            logging.error("Snow annual map cannot be computed because of too many missing products")

    def process_snow_products(self, file_to_process, array_size=None):
        logging.info("Ordering processing of the snow products on " + file_to_process)
        command = ["qsub",
                   "-v",
                   "filename=\""+file_to_process+"\",tile=\""+self.tile_id[1:]+"\",out_path=\""+self.snow_products_dir+"\",overwrite=\"false\"",
                   "run_lis_from_filelist.sh"]
        # in case the array size is provided, it requires a job array of the exact size.
        if array_size:
            command.insert(1, "-J")
            command.insert(2, "1-"+str(array_size+1))
        print(" ".join(command))
        try:
            call_subprocess(command)
            logging.info("Order was submitted the snow annual map will soon be available.")
        except:
            logging.warning("Order was submitted the snow annual map will soon be available, but missinterpreted return code")

    def process_snow_annual_map(self, file_to_process):
        logging.info("Ordering processing of the snow annual map, " + file_to_process)
        command = ["qsub",
                   "-v",
                   "config=\""+file_to_process+"\",overwrite=false",
                   "run_snow_annual_map.sh"]
        print(" ".join(command))
        try:
            call_subprocess(command)
            logging.info("Order was submitted the snow annual map will soon be available.")
        except:
            logging.warning("Order was submitted the snow annual map will soon be available, but missinterpreted return code")

def main():
    params = {"tile_id":"T32TPS",
              "date_start":"01/09/2017",
              "date_stop":"31/08/2018",
              "date_margin":15,
              "mode":"DEBUG",
              "input_products_list":[],
              # path_tmp is an actual parameter but must only be uncomment with a correct path
              # else the processing use $TMPDIR by default
              #"path_tmp":"",
              #"path_out":"/home/qt/salguesg/scratch/multitemp_workdir/tmp_test",
              "path_out":"/work/OT/siaa/Theia/Neige/SNOW_ANNUAL_MAP_LIS_1.5/L8_only",
              "ram":8192,
              "nbThreads":6,
              "use_densification":False,
              "log":True,
              "densification_products_list":[],
              # the following parameters are only use in this script, and doesn't affect snow_annual_map processing
              "snow_products_dir":"/work/OT/siaa/Theia/Neige/PRODUITS_NEIGE_LIS_develop_1.5",
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
                config_file = prepare_data_for_snow_annual_map_app.build_json()
                if config_file is not None:
                    prepare_data_for_snow_annual_map_app.process_snow_annual_map(config_file)

if __name__== "__main__":
    # Set logging level and format.
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=\
        '%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s')
    main()


