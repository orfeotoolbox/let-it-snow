import os
import sys
import os.path as op
import zipfile
import logging
from datetime import datetime
from os.path import basename, dirname

SNOW_PRODUCT_PATH = "/work/OT/siaa/Theia/S2L2A/data_production_muscate_juillet2017/L2B-SNOW"

MUSCATE_DATETIME_FORMAT = "%Y%m%d-%H%M%S-%f"
METADATA_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

def extract_from_zipfile(file_name, output_folder, patterns=[]):
    """ Extract from the zip file all files corresponding
    to on of the provided patterns
    """
    f = open(file_name,'r')
    z = zipfile.ZipFile(f)
    extracted_files = []
    for pattern in patterns:
        for name in z.namelist():
            if pattern in name:
                logging.debug(name)
                z.extract(name,output_folder)
                extracted_files.append(op.join(output_folder,name))
    f.close()
    return extracted_files

def str_to_datetime(date_string, format = MUSCATE_DATETIME_FORMAT):
    """ Return the datetime corresponding to the input string
    """
    logging.debug(date_string)
    return datetime.strptime(date_string, format)

def datetime_to_str(date, format = "%Y%m%d"):
    """ Return the datetime corresponding to the input string
    """
    logging.debug(date)
    return date.strftime(format)

def load_snow_product(absoluteFilename):
    pathname = dirname(absoluteFilename)
    filename = basename(absoluteFilename)

    # parse name to get metadata
    loaded_snow_product = snow_product(absoluteFilename)

    # parse files to get full metadata
    # @TODO 

    return loaded_snow_product

class snow_product:
    def __init__(self, absoluteFilename):
        # absoluteFilename example "SENTINEL2A_20160912-103551-370_L2B-SNOW_T32TLS_D_V1-0"

        self.product_name = basename(absoluteFilename)
        self.product_path = dirname(absoluteFilename)

        name_splitted = self.product_name.split("_")

        self.platform = name_splitted[0]
        self.acquisition_date = str_to_datetime(name_splitted[1], MUSCATE_DATETIME_FORMAT)
        self.product_level = name_splitted[2]
        self.tile_id = name_splitted[3]
        self.flag = name_splitted[4]
        self.product_version = name_splitted[5]

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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    a = snow_product("/work/OT/siaa/Theia/S2L2A/data_production_muscate_juillet2017/L2B-SNOW/SENTINEL2A_20170314-104411-573_L2B-SNOW_T31TGK_D_V1-0")
    print a.get_snow_mask()
    a.extract_snow_mask(".")
    print a.get_snow_mask()
    print a.get_metadata()
    print a.acquisition_date

    b = snow_product("./SENTINEL2A_20170314-104411-573_L2B-SNOW_T31TGK_D_V1-0")
    print a.get_snow_mask()
    a.extract_snow_mask(".")
    print a.get_snow_mask()
    print a.get_metadata()

if __name__ == '__main__':
    main()
