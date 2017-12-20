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
from lxml import etree
from xml.dom import minidom
from datetime import timedelta

import gdal
from gdalconst import GA_ReadOnly

# Build gdal option to generate maks of 1 byte using otb extended filename
# syntaxx
GDAL_OPT = "?&gdal:co:NBITS=1&gdal:co:COMPRESS=DEFLATE"

# OTB Applications
import otbApplication as otb

# Import python decorators for the different needed OTB applications
from s2snow.app_wrappers import band_math, get_app_output

from snow_product_parser import load_snow_product, str_to_datetime, datetime_to_str

def parse_xml(filepath):
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

def gap_filling(img_in, mask_in, img_out, input_dates_file = None,
                output_dates_file = None, ram=None, out_type=None):
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

def write_list_to_file(filename, str_list):
        output_file = open(filename, "w")
        output_file.write("\n".join(str_list))
        output_file.close()

def read_list_from_file(filename):
    output_file = open(filename, "r")
    lines = output_file.readlines()
    output_file.close()
    return [line.rstrip() for line in lines]

class snow_multitemp():
    def __init__(self, params):
        logging.info("Init snow_multitemp")

        self.tile_id = params.get("tile_id")
        self.date_start = params.get("date_start")
        self.date_stop = params.get("date_stop")
        self.mode = params.get("mode", "RUNTIME")

        self.input_dir = params.get("input_dir")
        self.path_tmp = params.get("path_tmp")

        self.path_out = op.join(params.get("path_out"),
                self.tile_id + "_" + datetime_to_str(self.date_start) +
                                        "-" + datetime_to_str(self.date_stop))

        if not os.path.exists(self.path_out):
            os.mkdir(self.path_out)

        self.ram = params.get("ram", 512)
        self.nbThreads = params.get("nbThreads", None)

        # Define label for output snow product
        self.label_no_snow = "0"
        self.label_snow = "100"
        self.label_cloud = "205"
        self.label_no_data = "254"

        # Build useful paths
        self.input_dates_filename = op.join(self.path_tmp, "input_dates.txt")
        self.output_dates_filename = op.join(self.path_tmp, "output_dates.txt")
        self.multitemp_snow_vrt = op.join(self.path_tmp, "multitemp_snow_mask.vrt")
        self.multitemp_cloud_vrt = op.join(self.path_tmp, "multitemp_cloud_mask.vrt")
        self.gapfilled_timeserie = op.join(self.path_tmp, "gap_filled_snow_mask.tif")
        self.annual_snow_map = op.join(self.path_tmp, "gap_filled_snow_mask_annual_snow.tif")

    def run(self):
        logging.info("Run snow_multitemp")

        # Set maximum ITK threads
        if self.nbThreads:
            os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(self.nbThreads)

        # search matching snow product
        self.product_list = self.find_products()
        logging.debug("Product list:")
        print self.product_list

        # re-order products according acquisition date
        self.product_list.sort(key=lambda x: x.acquisition_date)
        print self.product_list

        input_dates = []
        for product in self.product_list:
            input_dates.append(datetime_to_str(product.acquisition_date))
        write_list_to_file(self.input_dates_filename, input_dates)

        tmp_date = self.date_start
        output_dates = []
        while tmp_date < self.date_stop:
                output_dates.append(datetime_to_str(tmp_date))
                tmp_date += timedelta(days=1)

        ######################## to remove #######################
        # output_dates = read_list_from_file(os.path.join(self.path_out,"dates_S1_T31TGL.txt"))
        ######################## to remove #######################

        write_list_to_file(self.output_dates_filename, output_dates)


        shutil.copy2(self.input_dates_filename, self.path_out)
        shutil.copy2(self.output_dates_filename, self.path_out)

        # load required product
        self.snowmask_list = self.get_snow_masks()
        logging.debug("Snow mask list:")
        print self.snowmask_list

        # convert the snow masks into binary snow masks
        expression = "(im1b1==" + self.label_snow + ")?1:0"
        self.binary_snowmask_list = self.convert_mask_list(expression, "snow", GDAL_OPT)
        logging.debug("Binary snow mask list:")
        print self.binary_snowmask_list

        # convert the snow masks into binary cloud masks
        expression = "im1b1=="+self.label_cloud+"?1:(im1b1=="+self.label_no_data+"?1:0)"
        self.binary_cloudmask_list = self.convert_mask_list(expression, "cloud", GDAL_OPT)
        logging.debug("Binary cloud mask list:")
        print self.binary_cloudmask_list

        # build cloud mask vrt
        logging.info("Building multitemp cloud mask vrt")
        logging.info("cloud vrt: " + self.multitemp_cloud_vrt)
        gdal.BuildVRT(self.multitemp_cloud_vrt,
                      self.binary_cloudmask_list,
                      separate=True)

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

        img_in = get_app_output(app_gap_filling, "out", self.mode)

        if self.mode == "DEBUG":
            shutil.copy2(self.gapfilled_timeserie, self.path_out)
            app_gap_filling = None

        # generate the summary map
        band_index = range(1,len(output_dates)+1)
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

        logging.info("End snow_multitemp")

        if self.mode == "DEBUG":
            shutil.copytree(self.path_tmp, op.join(self.path_out, "tmpdir"))


    def find_products(self):
        logging.info("Retrieving products")
        product_files = os.listdir(self.input_dir)
        product_list = []
        for product_name in product_files:
            try:
                product = load_snow_product(op.join(self.input_dir, product_name))
                print product
                if self.tile_id in product.tile_id and \
                   self.date_start <= product.acquisition_date and \
                   self.date_stop >= product.acquisition_date:
                    product_list.append(product)
            except Exception:
                logging.error("Unable to load product :" + product_name)
        return product_list


    def get_snow_masks(self):
        return [i.get_snow_mask() for i in self.product_list]


    def convert_mask_list(self, expression, type_name, mask_format=""):
        binary_mask_list = []
        for product in self.product_list:
            mask_in = product.get_snow_mask()
            binary_mask = op.join(self.path_tmp, product.product_name + "_" + type_name + "_binary.tif")
            binary_mask = self.extract_binary_mask(mask_in, binary_mask, expression, mask_format)
            binary_mask_list.append(binary_mask)
        return binary_mask_list


    def extract_binary_mask(self, mask_in, mask_out, expression, mask_format=""):
        #if not os.path.exists(mask_out):
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
    params = {"tile_id":"T31TCH",
              "date_start":str_to_datetime("01/09/2015", "%d/%m/%Y"),
              "date_stop":str_to_datetime("31/08/2016", "%d/%m/%Y"),
              "mode":"DEBUG",
              "input_dir":"/work/OT/siaa/Theia/S2L2A/data_production_muscate_juillet2017/L2B-SNOW",
              "path_tmp":os.environ['TMPDIR'],
              "path_out":"/home/qt/salguesg/scratch/workdir",
              "ram":"2048",
              "nbThreads":5}

    # params["input_dir"] = "/work/OT/siaa/Theia/Neige/PRODUITS_NEIGE_2.4.5/T31TCH"
    params["input_dir"] = "/work/OT/siaa/Theia/Neige/output_muscate_v2pass2red40/T31TCH"


    #params = {"tile_id":"T32TLS",
              #"date_start":str_to_datetime("01/09/2015", "%d/%m/%Y"),
              #"date_stop":str_to_datetime("31/08/2016", "%d/%m/%Y"),
              #"mode":"DEBUG",
              #"input_dir":"/work/OT/siaa/Theia/Neige/output_muscate_v2pass2red40/T32TLS",
              #"path_tmp":os.environ['TMPDIR'],
              #"path_out":"/home/qt/salguesg/scratch/workdir",
              #"ram":"4096",
              #"nbThreads":8}


    multitempApp = snow_multitemp(params)
    multitempApp.run()

if __name__ == '__main__':
    # Set logging level and format.
    logging.basicConfig(level=logging.DEBUG, format=\
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()
