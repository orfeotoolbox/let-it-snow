#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import os.path as op
import sys
import uuid
import glob
import logging
import subprocess
from datetime import datetime
from shutil import copyfile
from distutils import spawn

import numpy as np

import gdal
import gdalconst
from gdalconst import GA_ReadOnly

# OTB Applications
import otbApplication as otb

# Import python decorators for the different needed OTB applications
from s2snow.app_wrappers import compute_contour, band_mathX


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

def write_list_to_file(filename, str_list):
    """ Write in a file a list of string as separate lines
    """
    output_file = open(filename, "w")
    output_file.write("\n".join(str_list))
    output_file.close()

def read_list_from_file(filename):
    """ Read file lines as a list of string removing end-of-line delimiters
    """
    output_file = open(filename, "r")
    lines = output_file.readlines()
    output_file.close()
    return [line.rstrip() for line in lines]

def polygonize(input_img, input_mask, output_vec, use_gina, min_area, dp_toler):
    """Helper function to polygonize raster mask using gdal polygonize

    if gina-tools is available it use gdal_trace_outline instead of
    gdal_polygonize (faster)
    """
    # Test if gdal_trace_outline is available
    gdal_trace_outline_path = spawn.find_executable("gdal_trace_outline")
    if not use_gina:
        # Use gdal_polygonize
        logging.info("Use gdal_polygonize to polygonize raster mask...")
        call_subprocess([
            "gdal_polygonize.py", input_img,
            "-f", "ESRI Shapefile",
            "-mask", input_mask, output_vec])
    elif use_gina and (gdal_trace_outline_path is None):
        logging.error("Cannot use gdal_trace_outline, executable not found on system!")
        logging.error("The vector file will not be generated.")
        logging.error("You can either disable the use_gdal_trace_outline option" \
                                    "or install the tools")
    else:
        logging.info("Use gdal_trace_outline to polygonize raster mask...")

        # Temporary file to store result of outline tool
        # Get unique identifier for the temporary file
        # Retrieve directory from input vector file
        input_dir = os.path.dirname(output_vec)
        unique_filename = uuid.uuid4()
        tmp_poly = op.join(input_dir, str(unique_filename))

        tmp_poly_shp = tmp_poly + ".shp"
        # We can use here gina-tools gdal_trace_outline which is faster
        command = [
            "gdal_trace_outline",
            input_img,
            "-classify",
            "-out-cs",
            "en",
            "-ogr-out",
            tmp_poly_shp,
            "-dp-toler",
            str(dp_toler),
            "-split-polys"]
        if min_area:
            command.extend(["-min-ring-area", str(min_area)])
        call_subprocess(command)

        # Then remove polygons with 0 as field value and rename field from
        # "value" to "DN" to follow same convention as gdal_polygonize
        call_subprocess([
            "ogr2ogr",
            "-sql",
            'SELECT value AS DN from \"' +
            str(unique_filename) +
            '\" where value != 0',
            output_vec,
            tmp_poly_shp])

        # Remove temporary vectors
        for shp in glob.glob(tmp_poly + "*"):
            os.remove(shp)


def composition_RGB(input_img, output_img, nSWIR, nRed, nGreen, multi):
    """Make a RGB composition to highlight the snow cover

    input_img: multispectral tiff, output_img: false color
    composite RGB image (GTiff).nRed,nGreen,nSWIR are index of red, green and
    SWIR in in put images.

    """
    scale_factor = 300 * multi

    gdal.Translate(output_img,
                   input_img,
                   format='GTiff',
                   creationOptions=['PHOTOMETRIC=RGB'],
                   outputType=gdal.GDT_Byte,
                   scaleParams=[[0,
                                 scale_factor,
                                 0,
                                 255]],
                   bandList=[nSWIR,
                             nRed,
                             nGreen])


def burn_polygons_edges(input_img, input_vec, snow_value, cloud_value, \
                        ram=None, fullyconnected=True):
    """Burn polygon borders onto an image with the following symbology:

    - cloud and cloud shadows: green
    - snow: magenta
    - convert mask polygons to lines
    - fullyconnected: True:8 connectivity, False:4 connectivity

    """

    # Prepare and execute the two contour extraction
    contourApp1 = compute_contour(input_vec, None, snow_value, \
                                  fullyconnected, ram)
    contourApp1.Execute()

    contourApp2 = compute_contour(input_vec, None, cloud_value, \
                                  fullyconnected, ram)
    contourApp2.Execute()

    # Prepare the BandMathX expression
    condition_shadow = "im1b1=="+snow_value+"?{255,0,255}:(im2b1=="+\
                       cloud_value+"?{0,255,0}:im3)"
    logging.info(condition_shadow)

    # Write the contours onto the composition
    bandMathFinalShadow = band_mathX(
        [contourApp1.GetParameterOutputImage("out"),
         contourApp2.GetParameterOutputImage("out"),
         input_img],
        input_img,
        condition_shadow,
        ram,
        otb.ImagePixelType_uint8)
    bandMathFinalShadow.ExecuteAndWriteOutput()


def extract_band(inputs, band, path_tmp, noData):
    """ Extract the required band using gdal.Translate
    """
    data_band = inputs[band]
    path = data_band["path"]
    band_no = data_band["noBand"]

    dataset = gdal.Open(path, GA_ReadOnly)
    path_extracted = op.join(path_tmp, band+"_extracted.tif")

    logging.info("extracting "+band)
    gdal.Translate(
            path_extracted,
            path,
            format='GTiff',
            outputType=gdal.GDT_Int16,
            noData=noData,
            bandList=[band_no])
 
    return path_extracted


def apply_color_table(raster_file_name, color_table):
    """ Edit image file to apply a color table
    """
    dataset = gdal.Open(raster_file_name, gdalconst.GA_Update)
    dataset.GetRasterBand(1).SetColorTable(color_table)
    dataset = None


def get_raster_as_array(raster_file_name):
    """ Open image file as numpy array using gdal
    """
    dataset = gdal.Open(raster_file_name, gdalconst.GA_ReadOnly)
    band = dataset.GetRasterBand(1)
    array = band.ReadAsArray()
    return array


def compute_percent(image_path, value, no_data=None):
    """ Compute the ocurrence of value as percentage in the input image
    """
    array_image = get_raster_as_array(image_path)
    tot_pix = array_image.size
    if no_data is not None:
        tot_pix = np.sum(array_image != int(no_data))

    if tot_pix != 0:
        count_pix = np.sum(array_image == int(value))
        return (float(count_pix) / float(tot_pix)) * 100
    else:
        return 0


def format_SEB_VEC_values(path, snow_label, cloud_label, nodata_label):
    """ Update the shapfile according lis product specifications
    """
    logging.info("Formatting snow/cloud shapefile")
    table = op.splitext(op.basename(path))[0]
    ds = gdal.OpenEx(path, gdal.OF_VECTOR | gdal.OF_UPDATE)
    ds.ExecuteSQL("ALTER TABLE " + table + " ADD COLUMN type varchar(15)")
    ds.ExecuteSQL("UPDATE " + table + " SET type='snow' WHERE DN="+\
                  snow_label, dialect="SQLITE")
    ds.ExecuteSQL("UPDATE " + table + " SET type='cloud' WHERE DN="+\
                  cloud_label, dialect="SQLITE")
    ds.ExecuteSQL("UPDATE " + table + " SET type='no data' WHERE DN == "+\
                  nodata_label, dialect="SQLITE")
