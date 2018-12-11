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
#=========================================================================
import os
import os.path as op
import shutil
import logging
import multiprocessing
from xml.dom import minidom
from datetime import timedelta

from lxml import etree

import gdal
from gdalconst import GA_ReadOnly

# OTB Applications
import otbApplication as otb

# Import python decorators for the different needed OTB applications
from s2snow.app_wrappers import band_math, get_app_output, super_impose

from s2snow.utils import str_to_datetime, datetime_to_str
from s2snow.utils import write_list_to_file, read_list_from_file
from s2snow.snow_product_parser import load_snow_product

# Build gdal option to generate maks of 1 byte using otb extended filename
# syntaxx
GDAL_OPT = "?&gdal:co:NBITS=1&gdal:co:COMPRESS=DEFLATE"

def parse_xml(filepath):
    """ Parse an xml file to return the zs value of a snow product
    """
    logging.debug("Parsing " + filepath)
    xmldoc = minidom.parse(filepath)
    group = xmldoc.getElementsByTagName('Global_Index_List')[0]
    zs = group.getElementsByTagName("QUALITY_INDEX")[0].firstChild.data

def findFiles(folder, pattern):
    """ Search recursively into a folder to find a patern match
    """
    matches = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if re.match(pattern, file):
                matches.append(os.path.join(root, file))
    return matches

def gap_filling(img_in, mask_in, img_out, input_dates_file=None,
                output_dates_file=None, ram=None, out_type=None):
    """ Create and configure the ImageTimeSeriesGapFilling application
        using otb.Registry.CreateApplication("ImageTimeSeriesGapFilling")

    Keyword arguments:
    img_in -- the input timeserie image
    mask_in -- the input masks
    img_out -- the output image
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if img_in and mask_in and img_out:
        logging.info("Processing ImageTimeSeriesGapFilling with args:")
        logging.info("img_in = " + img_in)
        logging.info("mask_in = " + mask_in)
        logging.info("img_out = " + img_out)

        gap_filling_app = otb.Registry.CreateApplication("ImageTimeSeriesGapFilling")
        gap_filling_app.SetParameterString("in", img_in)
        gap_filling_app.SetParameterString("mask", mask_in)
        gap_filling_app.SetParameterString("out", img_out)

        gap_filling_app.SetParameterInt("comp", 1)
        gap_filling_app.SetParameterString("it", "linear")

        if input_dates_file is not None:
            logging.info("input_dates_file = " + input_dates_file)
            gap_filling_app.SetParameterString("id", input_dates_file)
        if output_dates_file is not None:
            logging.info("output_dates_file = " + output_dates_file)
            gap_filling_app.SetParameterString("od", output_dates_file)
        if ram is not None:
            logging.info("ram = " + str(ram))
            gap_filling_app.SetParameterString("ram", str(ram))
        if out_type is not None:
            logging.info("out_type = " + str(out_type))
            gap_filling_app.SetParameterOutputImagePixelType("out", out_type)
        return gap_filling_app
    else:
        logging.error("Parameters img_in, img_out and mask_in are required")

def merge_masks_at_same_date(mask_snow_list, mask_cloud_list, merged_snow_mask, merged_cloud_mask):
        img_index = range(1, len(mask_cloud_list)+1)
        expression_cloud_merging = "".join(["(im" + str(i) + "b1==0?0:" for i in img_index])
        expression_cloud_merging += "1"
        expression_cloud_merging += "".join([")" for i in img_index])

        bandMathApp = band_math(mask_cloud_list,
                                merged_cloud_mask,
                                expression_cloud_merging,
                                self.ram,
                                otb.ImagePixelType_uint8)
        bandMathApp.ExecuteAndWriteOutput()
        bandMathApp = None

        offset = len(mask_cloud_list)
        expression_snow_merging = "".join(["(im" + str(i) + "b1==0?im"+str(i+offset)+"b1:" for i in img_index])
        expression_snow_merging += "0"
        expression_snow_merging += "".join([")" for i in img_index])

        input_img_list = mask_cloud_list + mask_snow_list;
        bandMathApp = band_math(input_img_list,
                                merged_snow_mask,
                                expression_snow_merging,
                                self.ram,
                                otb.ImagePixelType_uint8)
        bandMathApp.ExecuteAndWriteOutput()

class snow_annual_map():
    def __init__(self, params):
        logging.info("Init snow_multitemp")

        self.tile_id = params.get("tile_id")
        self.date_start = str_to_datetime(params.get("date_start"), "%d/%m/%Y")
        self.date_stop = str_to_datetime(params.get("date_stop"), "%d/%m/%Y")
        self.date_margin = timedelta(days=params.get("date_margin", 0))
        self.output_dates_filename = params.get("output_dates_filename", None)
        self.mode = params.get("mode", "RUNTIME")

        self.processing_id = str(self.tile_id + "_" + \
                             datetime_to_str(self.date_start) + "_" + \
                             datetime_to_str(self.date_stop))

        # input_dir is no longer used
        #self.input_dir = str(op.join(params.get("snow_products_dir"), self.tile_id))
        self.input_path_list = params.get("input_products_list", [])

        #self.path_tmp = str(params.get("path_tmp", os.environ.get('TMPDIR')))
        self.path_tmp = str(os.environ.get('TMPDIR'))
        self.path_out = op.join(str(params.get("path_out")), self.processing_id)

        if not os.path.exists(self.path_out):
            os.mkdir(self.path_out)

        self.ram = params.get("ram", 512)
        self.nbThreads = params.get("nbThreads", None)

        self.use_densification = params.get("use_densification", False)
        if self.use_densification:
            self.densification_path_list = params.get("densification_products_list", [])

        # Define label for output snow product
        self.label_no_snow = "0"
        self.label_snow = "100"
        self.label_cloud = "205"
        self.label_no_data = "254"

        # Build useful paths
        self.input_dates_filename = op.join(self.path_tmp, "input_dates.txt")
        if not self.output_dates_filename:
            self.output_dates_filename = op.join(self.path_tmp, "output_dates.txt")
        self.multitemp_snow_vrt = op.join(self.path_tmp, "multitemp_snow_mask.vrt")
        self.multitemp_cloud_vrt = op.join(self.path_tmp, "multitemp_cloud_mask.vrt")
        self.gapfilled_timeserie = op.join(self.path_tmp, "DAILY_SNOW_MASKS_" + self.processing_id + ".tif")
        self.annual_snow_map = op.join(self.path_tmp, "SNOW_OCCURENCE_" + self.processing_id + ".tif")
        self.cloud_occurence_img = op.join(self.path_tmp, "CLOUD_OCCURENCE_" + self.processing_id +".tif")

    def run(self):
        logging.info("Run snow_annual_map")

        # Set maximum ITK threads
        if self.nbThreads:
            os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(self.nbThreads)

        # search matching snow product
        self.product_list = self.load_products(self.input_path_list, self.tile_id, None)
        logging.debug("Product list:")
        logging.debug(self.product_list)

        if not self.product_list:
            logging.error("Empty product list!")
            return

        # @TODO clean the loading of the products to densify the timeserie
        if self.use_densification:
            # load densification snow products
            densification_product_list = self.load_products(self.densification_path_list, None, None)
            logging.info("Densification product list:")
            logging.info(densification_product_list)

            s2_input_dates = [datetime_to_str(product.acquisition_date) \
                              for product in self.product_list]
            s2_footprint_ref = self.product_list[0].get_snow_mask()

            # filter densification products to keep only products that don't overlap an existing S2 date
            final_densification_product_list = []
            for densifier_product in densification_product_list:
                if not datetime_to_str(densifier_product.acquisition_date) in s2_input_dates:
                    final_densification_product_list.append(densifier_product)
            logging.info(final_densification_product_list)

            
            if len(final_densification_product_list) > 0:

                # reproject the densification products on S2 tile before going further
                for densifier_product in final_densification_product_list:
                    original_mask = densifier_product.get_snow_mask()
                    reprojected_mask = op.join(self.path_tmp,
                                               densifier_product.product_name + "_reprojected.tif")
                    if not os.path.exists(reprojected_mask):
                        super_impose_app = super_impose(s2_footprint_ref,
                                                        original_mask,
                                                        reprojected_mask,
                                                        "nn",
                                                        int(self.label_no_data),
                                                        self.ram,
                                                        otb.ImagePixelType_uint8)
                        super_impose_app.ExecuteAndWriteOutput()
                        super_impose_app = None
                    densifier_product.snow_mask = reprojected_mask
                    logging.debug(densifier_product.snow_mask)

                logging.info("First densifying mask: " + final_densification_product_list[0].snow_mask)
                logging.info("Last densifying mask: " + final_densification_product_list[-1].snow_mask)
                self.product_list.extend(final_densification_product_list)
            else:
                logging.warning("No Densifying candidate product found!")

        # re-order products according acquisition date
        self.product_list.sort(key=lambda x: x.acquisition_date)
        logging.debug(self.product_list)

        input_dates = [datetime_to_str(product.acquisition_date) for product in self.product_list]
        write_list_to_file(self.input_dates_filename, input_dates)

        output_dates = []
        if op.exists(self.output_dates_filename):
            output_dates = read_list_from_file(self.output_dates_filename)
        else:
            tmp_date = self.date_start
            while tmp_date <= self.date_stop:
                output_dates.append(datetime_to_str(tmp_date))
                tmp_date += timedelta(days=1)
            write_list_to_file(self.output_dates_filename, output_dates)

        shutil.copy2(self.input_dates_filename, self.path_out)
        shutil.copy2(self.output_dates_filename, self.path_out)

        # load required product
        self.snowmask_list = self.get_snow_masks()
        logging.debug("Snow mask list:")
        logging.debug(self.snowmask_list)

        # convert the snow masks into binary snow masks
        expression = "(im1b1==" + self.label_snow + ")?1:0"
        self.binary_snowmask_list = self.convert_mask_list(expression, "snow", GDAL_OPT)
        logging.debug("Binary snow mask list:")
        logging.debug(self.binary_snowmask_list)

        # convert the snow masks into binary cloud masks
        expression = "im1b1=="+self.label_cloud+"?1:(im1b1=="+self.label_no_data+"?1:0)"
        self.binary_cloudmask_list = self.convert_mask_list(expression, "cloud", GDAL_OPT)
        logging.debug("Binary cloud mask list:")
        logging.debug(self.binary_cloudmask_list)

        # build cloud mask vrt
        logging.info("Building multitemp cloud mask vrt")
        logging.info("cloud vrt: " + self.multitemp_cloud_vrt)
        gdal.BuildVRT(self.multitemp_cloud_vrt,
                      self.binary_cloudmask_list,
                      separate=True)

        # generate the summary map
        band_index = range(1, len(self.binary_cloudmask_list)+1)
        expression = "+".join(["im1b" + str(i) for i in band_index])

        bandMathApp = band_math([self.multitemp_cloud_vrt],
                                self.cloud_occurence_img,
                                expression,
                                self.ram,
                                otb.ImagePixelType_uint16)
        bandMathApp.ExecuteAndWriteOutput()
        bandMathApp = None

        logging.info("Copying outputs from tmp to output folder")
        shutil.copy2(self.cloud_occurence_img, self.path_out)

        # build snow mask vrt
        logging.info("Building multitemp snow mask vrt")
        logging.info("snow vrt: " + self.multitemp_snow_vrt)
        gdal.BuildVRT(self.multitemp_snow_vrt,
                      self.binary_snowmask_list,
                      separate=True)

        # gap filling the snow timeserie
        app_gap_filling = gap_filling(self.multitemp_snow_vrt,
                                      self.multitemp_cloud_vrt,
                                      self.gapfilled_timeserie+GDAL_OPT,
                                      self.input_dates_filename,
                                      self.output_dates_filename,
                                      self.ram,
                                      otb.ImagePixelType_uint8)

        # @TODO the mode is for now forced to DEBUG in order to generate img on disk
        #img_in = get_app_output(app_gap_filling, "out", self.mode)
        #if self.mode == "DEBUG":
            #shutil.copy2(self.gapfilled_timeserie, self.path_out)
            #app_gap_filling = None

        img_in = get_app_output(app_gap_filling, "out", "DEBUG")
        shutil.copy2(self.gapfilled_timeserie, self.path_out)
        app_gap_filling = None

        # generate the summary map
        band_index = range(1, len(output_dates)+1)
        expression = "+".join(["im1b" + str(i) for i in band_index])

        bandMathApp = band_math([img_in],
                                self.annual_snow_map,
                                expression,
                                self.ram,
                                otb.ImagePixelType_uint16)
        bandMathApp.ExecuteAndWriteOutput()
        bandMathApp = None

        logging.info("Copying outputs from tmp to output folder")
        shutil.copy2(self.annual_snow_map, self.path_out)

        logging.info("End of snow_annual_map")

        if self.mode == "DEBUG":
            dest_debug_dir = op.join(self.path_out, "tmpdir")
            if op.exists(dest_debug_dir):
                shutil.rmtree(shutil)
            shutil.copytree(self.path_tmp, dest_debug_dir)

    def load_products(self, snow_products_list, tile_id=None, product_type=None):
        logging.info("Parsing provided snow products list")
        product_list = []
        search_start_date = self.date_start - self.date_margin
        search_stop_date = self.date_stop + self.date_margin
        for product_path in snow_products_list:
            try:
                product = load_snow_product(str(product_path))
                logging.info(str(product))
                test_result = True
                if search_start_date > product.acquisition_date or \
                   search_stop_date < product.acquisition_date:
                   test_result = False
                if (tile_id is not None) and (tile_id not in product.tile_id):
                   test_result = False
                if (product_type is not None) and (product_type not in product.platform):
                   test_result = False
                if test_result:
                    product_list.append(product)
                    logging.info("Keeping: " + str(product))
                else:
                    logging.warning("Discarding: " + str(product))
            except Exception:
                logging.error("Unable to load product :" + product_path)
        return product_list


    def get_snow_masks(self):
        return [i.get_snow_mask() for i in self.product_list]


    def convert_mask_list(self, expression, type_name, mask_format=""):
        binary_mask_list = []
        for product in self.product_list:
            mask_in = product.get_snow_mask()
            binary_mask = op.join(self.path_tmp,
                                  product.product_name + "_" + type_name + "_binary.tif")
            binary_mask = self.extract_binary_mask(mask_in,
                                                   binary_mask,
                                                   expression,
                                                   mask_format)
            binary_mask_list.append(binary_mask)
        return binary_mask_list


    def extract_binary_mask(self, mask_in, mask_out, expression, mask_format=""):
        bandMathApp = band_math([mask_in],
                                mask_out + mask_format,
                                expression,
                                self.ram,
                                otb.ImagePixelType_uint8)
        bandMathApp.ExecuteAndWriteOutput()
        return mask_out

###############################################################
#   Main Test
###############################################################
def main():

    params = {"tile_id":"T32TPS",
              "date_start":"01/09/2017",
              "date_stop":"31/08/2018",
              "date_margin":15,
              "mode":"DEBUG",
              "input_products_list":[],
              "snow_products_dir":"/work/OT/siaa/Theia/Neige/PRODUITS_NEIGE_LIS_develop_1.5",
              "path_tmp":"",
              "path_out":"/work/OT/siaa/Theia/Neige/Snow_Annual_Maps_FIX/tmp",
              "ram":4096,
              "nbThreads":6,
              "use_densification":True,
              "densification_products_list":[],
              "data_availability_check":False}

    snow_annual_map_app = snow_annual_map(params)
    snow_annual_map_app.run()

if __name__ == '__main__':
    # Set logging level and format.
    logging.basicConfig(level=logging.DEBUG, format=\
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()
