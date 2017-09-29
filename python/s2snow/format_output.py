import sys
import subprocess
import glob
import os
import os.path as op
import glob
import datetime
import logging
from lxml import etree
from shutil import move, copyfile
import gdal
import gdalconst
import numpy as np

from app_wrappers import band_math
# OTB Applications
import otbApplication as otb

def get_raster_as_array(raster_file_name):
    dataset = gdal.Open(raster_file_name, gdalconst.GA_ReadOnly)
    band = dataset.GetRasterBand(1)
    array = band.ReadAsArray()
    return array

def compute_percent(image_path, value, no_data):
    array_image = get_raster_as_array(image_path)
    count_pix = np.sum(array_image == int(value))
    tot_pix = np.sum(array_image != int(no_data))
    return (float(count_pix) / float(tot_pix)) * 100

def format_LIS(snow_detector):
    path_img = snow_detector.img
    pout = snow_detector.path_tmp
    zs = snow_detector.zs
    ram = snow_detector.ram
    product_id = op.splitext(op.basename(path_img))[0]

    # Prepare product directory
    path_products = op.join(pout, "LIS_PRODUCTS")
    if not op.exists(path_products):
        os.makedirs(path_products)

    snow_percent = compute_percent(snow_detector.final_mask_path,
                                    snow_detector.label_snow,
                                    snow_detector.label_no_data)
    logging.info("Snow percent =" + str(snow_percent))

    cloud_percent = compute_percent(snow_detector.final_mask_path,
                                    snow_detector.label_cloud,
                                    snow_detector.label_no_data)
    logging.info("Cloud percent =" + str(cloud_percent))

    code_metadata = "_METADATA"
    str_metadata = (product_id + code_metadata + ".xml").upper()

    root = etree.Element("Source_Product")
    etree.SubElement(root, "PRODUCT_ID").text = product_id
    egil = etree.SubElement(root, "Global_Index_List")
    etree.SubElement(egil, "QUALITY_INDEX", name='ZS').text = str(zs)
    etree.SubElement(
        egil,
        "QUALITY_INDEX",
        name='SnowPercent').text = str(snow_percent)
    etree.SubElement(
        egil,
        "QUALITY_INDEX",
        name='CloudPercent').text = str(cloud_percent)
    et = etree.ElementTree(root)
    et.write(op.join(path_products, str_metadata), pretty_print=True)

    ext = "TIF"
    code_snow_all = "_SNOW_ALL"
    str_snow_all = (product_id + code_snow_all + "." + ext).upper()
    move(snow_detector.snow_all_path,
             op.join(path_products, str_snow_all))

    code_seb = "_SEB"
    str_seb = (product_id + code_seb + "." + ext).upper()
    move(snow_detector.final_mask_path,
             op.join(path_products, str_seb))

    code_seb_vec = "_SEB_VEC"
    for f in glob.glob(op.join(pout, "final_mask_vec.*")):
        extension = op.splitext(f)[1]
        str_seb_vec = (product_id + code_seb_vec + extension).upper()
        if extension == ".shp":
            format_SEB_VEC_values(f,
                                  snow_detector.label_snow,
                                  snow_detector.label_cloud,
                                  snow_detector.label_no_data)
        copyfile(f, op.join(path_products, str_seb_vec))

    code_compo = "_COMPO"
    str_compo = (product_id + code_compo + ".tif").upper()
    move(snow_detector.composition_path, 
             op.join(path_products, str_compo))

    # Copy histogram to LIS_PRODUCTS directory
    ext = "TXT"
    code_histo = "_HISTO"
    str_histo = (product_id + code_histo + "." + ext).upper()
    move(snow_detector.histogram_path,
             op.join(path_products, str_histo))

def format_SEB_VEC_values(path, snow_label, cloud_label, nodata_label):
    table = op.splitext(op.basename(path))[0]
    ds = gdal.OpenEx(path, gdal.OF_VECTOR | gdal.OF_UPDATE)
    ds.ExecuteSQL("ALTER TABLE " + table + " ADD COLUMN type varchar(15)")
    ds.ExecuteSQL("UPDATE " + table + " SET type='snow' WHERE DN="+snow_label, dialect="SQLITE")
    ds.ExecuteSQL("UPDATE " + table + " SET type='cloud' WHERE DN="+cloud_label, dialect="SQLITE")
    ds.ExecuteSQL("UPDATE " + table + " SET type='no data' WHERE DN == "+nodata_label, dialect="SQLITE")
