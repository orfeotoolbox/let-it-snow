#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import os.path as op
from os.path import basename, dirname
import zipfile
import logging

from s2snow.utils import str_to_datetime

MUSCATE_DATETIME_FORMAT = "%Y%m%d-%H%M%S-%f"
METADATA_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

def extract_from_zipfile(file_name, output_folder, patterns=[]):
    """ Extract from the zip file all files corresponding
    to on of the provided patterns
    """
    f = open(file_name, 'r')
    z = zipfile.ZipFile(f)
    extracted_files = []
    for pattern in patterns:
        for name in z.namelist():
            if pattern in name:
                logging.debug(name)
                z.extract(name, output_folder)
                extracted_files.append(op.join(output_folder, name))
    f.close()
    return extracted_files

def load_snow_product(absolute_filename):
    pathname = dirname(absolute_filename)
    filename = basename(absolute_filename)

    # parse name to get metadata
    loaded_snow_product = snow_product(absolute_filename)

    # parse files to get full metadata
    # @TODO

    return loaded_snow_product

class snow_product:
    def __init__(self, absoluteFilename):
        # example 1 "SENTINEL2A_20160912-103551-370_L2B-SNOW_T32TLS_D_V1-0"
        # example 2 "LANDSAT8_OLITIRS_XS_20160812_N2A_France-MetropoleD0005H0001"

        self.product_name = basename(absoluteFilename)
        self.product_path = dirname(absoluteFilename)

        name_splitted = self.product_name.split("_")

        self.platform = name_splitted[0]
        if "SENTINEL2" in self.platform:
            self.acquisition_date = str_to_datetime(name_splitted[1], MUSCATE_DATETIME_FORMAT)
            self.product_level = name_splitted[2]
            self.tile_id = name_splitted[3]
            self.flag = name_splitted[4]
            self.product_version = name_splitted[5]
        elif "LANDSAT8-OLITIRS-XS" == self.platform:
            self.acquisition_date = str_to_datetime(name_splitted[1], MUSCATE_DATETIME_FORMAT)
            self.product_level = name_splitted[2]
            self.tile_id = name_splitted[3]
            self.flag = name_splitted[4]
            self.product_version = name_splitted[5]
        elif "LANDSAT8" in self.platform and "N2A" in self.product_name:
            self.acquisition_date = str_to_datetime(name_splitted[3], "%Y%m%d")
            self.product_level = name_splitted[4]
            self.tile_id = name_splitted[5]
            self.flag = None
            self.product_version = None
        else:
            logging.error("Unknown platform: " + self.platform)
            raise Exception()

        logging.debug("New snow_product:")
        logging.debug(absoluteFilename)
        logging.debug(str(self.acquisition_date))
        logging.debug(self.tile_id)

        self.zip_product = None
        self.is_extracted = False
        self.snow_mask = None

        self.sub_files = os.listdir(absoluteFilename)
        for sub_file in self.sub_files:
            if sub_file.lower().endswith(".zip"):
                logging.info("The snow product is stored in a zip")
                self.zip_product = op.join(absoluteFilename, sub_file)
            if sub_file == self.product_name:
                logging.info("The zipped snow product is already extracted")
                self.is_extracted = True
                self.extracted_product = op.join(absoluteFilename, sub_file)
                self.snow_mask = op.join(self.extracted_product,
                                         self.product_name + "_SNW_R2.tif")
            if sub_file.upper().endswith("_SNW_R2.TIF"):
                self.is_extracted = True
                self.snow_mask = op.join(absoluteFilename, sub_file)
            if sub_file.upper() == "LIS_PRODUCTS":
                self.is_extracted = True
                self.extracted_product = op.join(absoluteFilename, sub_file)
                self.snow_mask = op.join(self.extracted_product, "LIS_SEB.TIF")

        self.metadata_file = op.join(absoluteFilename,
                                     self.product_name + "_MTD_ALL.xml")

    def __repr__(self):
        return op.join(self.product_path, self.product_name)

    def __str__(self):
        return op.join(self.product_path, self.product_name)

    def extract_snow_mask(self, output_folder):
        if self.snow_mask and op.exists(self.snow_mask):
            logging.info("The snow mask is already extracted and available")
        elif self.zip_product and op.exists(self.zip_product):
            extracted_files = extract_from_zipfile(self.zip_product,
                                                   output_folder,
                                                   ["_SNW_R2.tif"])
            self.snow_mask = extracted_files[0]
        else:
            logging.error("Extraction failed")

    def get_snow_mask(self):
        if self.snow_mask and op.exists(self.snow_mask):
            return self.snow_mask
        else:
            logging.info("The snow mask must first be extracted")

    def get_metadata(self):
        if self.metadata_file and op.exists(self.metadata_file):
            return self.metadata_file
        else:
            logging.info("The metadata file was not found")


###############################################################
#   Main Test
###############################################################
def main():

    # Set logging level and format.
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    a = snow_product("/work/OT/siaa/Theia/S2L2A/data_production_muscate_juillet2017/L2B-SNOW/SENTINEL2A_20170314-104411-573_L2B-SNOW_T31TGK_D_V1-0")
    print(a.get_snow_mask())
    a.extract_snow_mask(".")
    print(a.get_snow_mask())
    print(a.get_metadata())
    print(a.acquisition_date)

    b = snow_product("/work/OT/siaa/Theia/Neige/output_muscate_v2pass2red40/T31TGL/SENTINEL2A_20151230-105153-392_L2A_T31TGL_D_V1-0")
    print(b.get_snow_mask())
    b.extract_snow_mask(".")
    print(b.get_snow_mask())
    print(b.get_metadata())

    c = snow_product("/work/OT/siaa/Theia/Neige/output_muscate_v2pass2red40/Landsat-8/D0005H0001/LANDSAT8_OLITIRS_XS_20160812_N2A_France-MetropoleD0005H0001")
    print(c.get_snow_mask())
    c.extract_snow_mask(".")
    print(c.get_snow_mask())
    print(c.get_metadata())

if __name__ == '__main__':
    main()
