import sys
import subprocess 
import glob
import os
import os.path as op
import glob
import datetime
from lxml import etree
from shutil import copyfile
import gdal
import gdalconst
import numpy as np

# run subprocess and write to stdout and stderr
def call_subprocess(process_list):
    process = subprocess.Popen(process_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    print out
    sys.stderr.write(err)

def get_raster_as_array(raster_file_name):
	dataset = gdal.Open(raster_file_name, gdalconst.GA_ReadOnly)    
	wide = dataset.RasterXSize
	high = dataset.RasterYSize
	band = dataset.GetRasterBand(1)
	array = band.ReadAsArray(0, 0, wide, high)
	return array, dataset

def compute_cloudpercent(image_path):
	array_image, dataset_image = get_raster_as_array(image_path)
	cloud = np.sum(array_image == 205)
	tot_pix = np.sum(array_image != 254)
	return (float(cloud)/float(tot_pix))*100

def compute_snowpercent(image_path):
	array_image, dataset_image = get_raster_as_array(image_path)
	cloud = np.sum(array_image == 100)
	tot_pix = np.sum(array_image != 254)
	return (float(cloud)/float(tot_pix))*100

def format_LIS(snow_detector):
	path_img = snow_detector.img
	pout = snow_detector.path_tmp
	zs = snow_detector.zs
	ram = snow_detector.ram
	mode = snow_detector.mode
	nodata_path = snow_detector.nodata_path
	
	if mode == "s2":
        #ID corresponding to the parent folder of the img
		product_id = op.basename(op.abspath(op.join(path_img, os.pardir)))
	else:
		#ID corresponding to the name of the img
		product_id = op.splitext(op.basename(path_img))[0]

	ext = "TIF"
   
    #TODO associate product name with let-it-snow results to make a loop
	code_snow_all = "_SNOW_ALL"
	str_snow_all = product_id+code_snow_all+"."+ext 
	str_snow_all = str_snow_all.upper()
	copyfile(op.join(pout, "snow_all.tif"), op.join(pout, str_snow_all))
	
	code_compo = "_COMPO"
	str_compo = product_id+code_compo+"."+ext
	str_compo = str_compo.upper()
	copyfile(op.join(pout, "composition.tif"), op.join(pout, str_compo))
	
	code_seb = "_SEB"
	str_seb = product_id+code_seb+"."+ext 
	str_seb = str_seb.upper()
	format_SEB_values(op.join(pout, "final_mask.tif"), nodata_path, ram)
	copyfile(op.join(pout, "final_mask.tif"), op.join(pout, str_seb))
	
	code_seb_vec = "_SEB_VEC"
	for f in glob.glob(op.join(pout, "final_mask_vec.*")):
		extension = op.splitext(f)[1]
		str_seb_vec = product_id+code_seb_vec+extension
		str_seb_vec = str_seb_vec.upper()
		if extension == ".dbf":
			format_SEB_VEC_values(f)
		copyfile(f, op.join(pout, str_seb_vec))
	
	snow_percent = compute_snowpercent(op.join(pout, "final_mask.tif"))
	cloud_percent = compute_cloudpercent(op.join(pout, "final_mask.tif"))
	
	root = etree.Element("Source_Product")
	etree.SubElement(root, "PRODUCT_ID").text = product_id
	egil = etree.SubElement(root, "Global_Index_List")
	etree.SubElement(egil, "QUALITY_INDEX", name='ZS').text = str(zs)
	etree.SubElement(egil, "QUALITY_INDEX", name='SnowPercent').text = str(snow_percent)
	etree.SubElement(egil, "QUALITY_INDEX", name='CloudPercent').text = str(cloud_percent)
	et = etree.ElementTree(root)
	et.write(op.join(pout, "metadata.xml"), pretty_print = True)
	code_metadata = "_METADATA"
	str_metadata = product_id+code_metadata+".xml"
	str_metadata = str_metadata.upper()
	copyfile(op.join(pout, "metadata.xml"), op.join(pout, str_metadata))
	
def format_SEB_values(path, nodata_path, ram):
	call_subprocess(["otbcli_BandMath", "-il", path, "-out", path, "uint8", "-ram",str(ram), "-exp", "(im1b1==1)?100:(im1b1==2)?205:0"])
	call_subprocess(["otbcli_BandMath", "-il", path, nodata_path, "-out", path, "uint8", "-ram" , str(ram), "-exp", "im2b1==1?254:im1b1"])
	
def format_SEB_VEC_values(path):
	table = op.splitext(op.basename(path))[0]
	call_subprocess(["ogrinfo", path, "-sql", "ALTER TABLE "+table+" ADD COLUMN type varchar(15)"]) 
	call_subprocess(["ogrinfo", path, "-dialect", "SQLite", "-sql", "UPDATE '"+table+"' SET DN=100, type='snow' WHERE DN=1"])
	call_subprocess(["ogrinfo", path, "-dialect", "SQLite", "-sql", "UPDATE '"+table+"' SET DN=205, type='cloud' WHERE DN=2"])
	call_subprocess(["ogrinfo", path, "-dialect", "SQLite", "-sql", "UPDATE '"+table+"' SET DN=254, type='no data' WHERE DN != 100 AND DN != 205"])
        
