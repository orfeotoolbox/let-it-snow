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

# Build gdal option to generate maks of 2 bytes using otb extended filename
# syntax
GDAL_OPT_2B = "?&gdal:co:NBITS=2&gdal:co:COMPRESS=DEFLATE"

# OTB Applications
import otbApplication as otb

# Import python decorators for the different needed OTB applications
from s2snow.app_wrappers import band_math, get_app_output

from snow_product_parser import load_snow_product, str_to_datetime, datetime_to_str

from snow_multitemp import snow_multitemp, write_list_to_file

def read_list_from_file(filename):
    output_file = open(filename, "r")
    lines = output_file.readlines()
    output_file.close()
    return [line.rstrip() for line in lines]


def super_impose(img_in, mask_in, img_out, interpolator = None,
                fill_value=None, ram=None, out_type=None):
    """ Create and configure the otbSuperImpose application
        using otb.Registry.CreateApplication("Superimpose")

    Keyword arguments:
    img_in -- the reference image in
    mask_in -- the input mask to superimpose on img_in
    img_out -- the output image
    fill_value -- the fill value for area outside the reprojected image
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if img_in and mask_in and img_out:
        logging.info("Processing otbSuperImpose with args:")
        logging.info("img_in = " + img_in)
        logging.info("mask_in = " + mask_in)
        logging.info("img_out = " + img_out)
        logging.info("interpolator = " + interpolator)

        super_impose_app = otb.Registry.CreateApplication("Superimpose")
        super_impose_app.SetParameterString("inr", img_in)
        super_impose_app.SetParameterString("inm", mask_in)
        super_impose_app.SetParameterString("out", img_out)
        super_impose_app.SetParameterString("interpolator", "linear")
        
        if fill_value is not None:
            logging.info("fill_value = " + str(fill_value))
            super_impose_app.SetParameterFloat("fv", fill_value)
        if ram is not None:
            logging.info("ram = " + str(ram))
            super_impose_app.SetParameterString("ram", str(ram))
        if out_type is not None:
            logging.info("out_type = " + str(out_type))
            super_impose_app.SetParameterOutputImagePixelType("out", out_type)
        return super_impose_app
    else:
        logging.error("Parameters img_in, img_out and mask_in are required")

def confusion_matrix(img_in, ref_in, out, ref_no_data=None, ram=None):
    """ Create and configure the otbComputeConfusionMatrix application
        using otb.Registry.CreateApplication("ComputeConfusionMatrix")

    Keyword arguments:
    img_in -- the image in
    out -- the matrix output
    ref_in -- the reference image in
    ref_no_data -- the nodata value for  pixels in ref raster
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if img_in and ref_in and out:
        logging.info("Processing otbComputeConfusionMatrix with args:")
        logging.info("img_in = " + img_in)
        logging.info("out = " + out)
        logging.info("ref_in = " + ref_in)

        super_impose_app = otb.Registry.CreateApplication("ComputeConfusionMatrix")
        super_impose_app.SetParameterString("in", img_in)
        super_impose_app.SetParameterString("ref", "raster")
        super_impose_app.SetParameterString("ref.raster.in", ref_in)
        super_impose_app.SetParameterString("out", out)

        if ref_no_data is not None:
            logging.info("ref_no_data = " + str(ref_no_data))
            super_impose_app.SetParameterInt("ref.raster.nodata", ref_no_data)
        if ram is not None:
            logging.info("ram = " + str(ram))
            super_impose_app.SetParameterString("ram", str(ram))
        return super_impose_app
    else:
        logging.error("Parameters img_in, out and ref_in are required")

class snow_multitemp_eveluation(snow_multitemp):
    def __init__(self, params):
        logging.info("Init snow_multitemp_evaluation")

        # inherit from snow_multitemp all the methods and variables
        snow_multitemp.__init__(self, params)

        self.tile_id = params.get("l8_tile_id")
        self.input_dir = params.get("l8_input_dir")

        # Build useful paths
        self.l8_dates_filename = op.join(self.path_tmp, "l8_inputs_dates.txt")
        self.l8_multitemp_snow_vrt = op.join(self.path_tmp, "l8_multitemp_snow_mask.vrt")
        self.l8_multitemp_cloud_vrt = op.join(self.path_tmp, "l8_multitemp_cloud_mask.vrt")

    def run(self):
        logging.info("Run snow_multitemp_evaluation")

        # Set maximum ITK threads
        if self.nbThreads:
            os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(self.nbThreads)

        # search matching L8 snow product
        self.product_list = self.find_products()
        logging.debug("Product list:")
        print self.product_list

        # re-order products according acquisition date
        self.product_list.sort(key=lambda x: x.acquisition_date)
        logging.debug("Sorted product list:")
        print self.product_list

        # create the l8 products dates file
        l8_input_dates = []
        for product in self.product_list:
            l8_input_dates.append(datetime_to_str(product.acquisition_date))
        write_list_to_file(self.l8_dates_filename, l8_input_dates)

        # load required product
        self.snowmask_list = self.get_snow_masks()
        logging.debug("L8 snow mask list:")
        print self.snowmask_list

        # convert the snow masks into binary snow masks
        expression = "im1b1=="+self.label_cloud+"?2:(im1b1=="+self.label_no_data+"?2:(im1b1==" + self.label_snow + ")?1:0)"
        self.binary_snowmask_list = self.convert_mask_list(expression, "snow")
        logging.debug("Binary snow mask list:")
        print self.binary_snowmask_list

        # pair the matching products
        ts_dates = read_list_from_file(self.output_dates_filename)
        date_index = 0
        pair_dict = {}
        for date_index in range(0,len(ts_dates)):
            for l8_date in l8_input_dates:
                if ts_dates[date_index] in l8_date:
                    pair_dict[l8_date] = date_index
        print pair_dict

        # project the snow masks onto the same foot print
        self.binary_snowmask_list_reprojected = []
        for mask_in in self.binary_snowmask_list:
            mask_out = mask_in.replace(".tif", "_reprojected.tif")
            if not os.path.exists(mask_out):
                super_impose_app = super_impose(self.annual_snow_map,
                                                mask_in,
                                                mask_out+GDAL_OPT_2B,
                                                "linear",
                                                2,
                                                self.ram,
                                                otb.ImagePixelType_uint8)
                super_impose_app.ExecuteAndWriteOutput()
                super_impose_app = None
            self.binary_snowmask_list_reprojected.append(mask_out)

        # compare the two snow masks
        l8_index = 0
        for l8_date in l8_input_dates:
            s2_index = pair_dict[l8_date]

            path_extracted = op.join(self.path_tmp, "gapfilled_s2_" + l8_date + ".tif")
            gdal.Translate(
                path_extracted,
                self.gapfilled_timeserie,
                format='GTiff',
                outputType=gdal.GDT_Byte,
                noData=None,
                bandList=[s2_index+1])

            expression = "im2b1==2?254:(2*im2b1+im1b1)"
            img_out = op.join(self.path_tmp, "comparision_" + l8_date + ".tif")
            bandMathApp = band_math([path_extracted,
                                     self.binary_snowmask_list_reprojected[l8_index]],
                                    img_out,
                                    expression,
                                    self.ram,
                                    otb.ImagePixelType_uint8)
            bandMathApp.ExecuteAndWriteOutput()
            bandMathApp = None

            shutil.copy2(img_out, self.path_out)

            out = op.join(self.path_tmp, "confusion_matrix_"+ l8_date + ".csv")
            confusionMatrixApp = confusion_matrix(
                                    path_extracted,
                                    self.binary_snowmask_list_reprojected[l8_index],
                                    out,
                                    2,
                                    self.ram)
            confusionMatrixApp.ExecuteAndWriteOutput()
            confusionMatrixApp = None

            shutil.copy2(out, self.path_out)

            l8_index+=1

        # gather stats
        # @TODO use otbcli_ComputeConfusionMatrix with 
        logging.info("End snow_multitemp_evaluation")

    def compare_modis(self):
        modis_snowserie = os.path.join("/work/OT/siaa/Theia/Neige/MODIS/export2017","Pirineos_gapfilled.tif")
        modis_datefile = os.path.join("/work/OT/siaa/Theia/Neige/MODIS/export2017","Pirineos_gapfilled_dates.csv")
        modis_start_index = None
        modis_stop_index = None

        self.modis_annual_snow_map = op.join(self.path_tmp, "modis_annual_snowmap.tif")

        modis_dates = read_list_from_file(modis_datefile)
        for i in range(0,len(modis_dates)):
            tmp_date = str_to_datetime(modis_dates[i], "%Y,%m,%d")
            if tmp_date == self.date_start:
                modis_start_index = i
            if tmp_date == self.date_stop:
                modis_stop_index = i

        # generate the summary map
        band_index = range(modis_start_index+1,modis_stop_index+2)
        expression = "+".join(["(im1b" + str(i) + "==200?1:0)" for i in band_index])

        bandMathApp = band_math([modis_snowserie],
                                self.modis_annual_snow_map,
                                expression,
                                self.ram,
                                otb.ImagePixelType_uint16)
        bandMathApp.ExecuteAndWriteOutput()
        bandMathApp = None

        shutil.copy2(self.modis_annual_snow_map, self.path_out)

        reprojected_snow_map = self.annual_snow_map.replace(".tif", "_reprojected.tif")
        super_impose_app = super_impose(self.modis_annual_snow_map,
                                        self.annual_snow_map,
                                        reprojected_snow_map,
                                        "linear",
                                        0,
                                        self.ram,
                                        otb.ImagePixelType_uint16)
        super_impose_app.ExecuteAndWriteOutput()
        super_impose_app = None
        shutil.copy2(reprojected_snow_map, self.path_out)

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
              "ram":"4096",
              "nbThreads":8,
              "l8_tile_id":"D0005H0001",
              "l8_input_dir":"/work/OT/siaa/Theia/Neige/output_muscate_v2pass2red40/Landsat-8/D0005H0001"}

    # params["input_dir"] = "/work/OT/siaa/Theia/Neige/PRODUITS_NEIGE_2.4.5/T31TCH"
    params["input_dir"] = "/work/OT/siaa/Theia/Neige/output_muscate_v2pass2red40/T31TCH"
    
    multitempApp = snow_multitemp_eveluation(params)
    # multitempApp.run()
    multitempApp.compare_modis()

if __name__ == '__main__':
    # Set logging level and format.
    logging.basicConfig(level=logging.DEBUG, format=\
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()

