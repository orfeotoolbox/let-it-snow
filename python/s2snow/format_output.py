import sys
from subprocess import call
import glob
import os
import os.path as op
import glob
import datetime
from lxml import etree
from shutil import copyfile
import gdal

def format_LIS(snow_detector):
    path_img = snow_detector.img
    pout = snow_detector.path_tmp
    zs = snow_detector.zs
    snow_percent = snow_detector.snow_percent
    cloud_percent = snow_detector.cloud_percent
    ram = snow_detector.ram
    mode = snow_detector.mode
    
    if mode == "s2":
        #ID corresponding to the parent folder of the img
        product_id = op.basename(op.abspath(op.join(path_img, os.pardir)))
    else:
        #ID corresponding to the name of the img
        product_id = op.splitext(op.basename(path_img))[0]

    ext = "TIF"
   
    #TODO associate product name with let-it-snow results to make a loop
    code_snow_all = "_SNOW_ALL_"
    str_snow_all = product_id+"_"+code_snow_all+"."+ext 
    str_snow_all = str_snow_all.upper()
    os.rename(op.join(pout, "snow_all.tif"), op.join(pout, str_snow_all))

    code_compo = "_COMPO_"
    str_compo = product_id+"_"+code_compo+"."+ext
    str_compo = str_compo.upper()
    os.rename(op.join(pout, "quicklook.tif"), op.join(pout, str_compo))
    
    code_seb = "_SEB_"
    str_seb = product_id+"_"+code_seb+"."+ext 
    str_seb = str_seb.upper()
    os.rename(op.join(pout, "final_mask.tif"), op.join(pout, str_seb))
    format_SEB_values(op.join(pout, str_seb), ram)
    
    code_seb_vec = "_SEB_VEC_"
    for f in glob.glob(op.join(pout, "final_mask_vec.*")):
        extension = op.splitext(f)[1]
        str_seb_vec = product_id+"_"+code_seb_vec+extension
        str_seb_vec = str_seb_vec.upper()
        os.rename(f, op.join(pout, str_seb_vec))
        if extension == ".dbf":
            format_SEB_VEC_values(op.join(pout, str_seb_vec))
    
    root = etree.Element("Source_Product")
    etree.SubElement(root, "PRODUCT_ID").text = product_id
    egil = etree.SubElement(root, "Global_Index_List")
    etree.SubElement(egil, "QUALITY_INDEX", name='ZS').text = str(zs)
    etree.SubElement(egil, "QUALITY_INDEX", name='SnowPercent').text = str(snow_percent)
    etree.SubElement(egil, "QUALITY_INDEX", name='CloudPercent').text = str(cloud_percent)
    et = etree.ElementTree(root)
    et.write(op.join(pout, "metadata.xml"), pretty_print = True)
    

def format_SEB_values(path, ram):
    call(["otbcli_BandMath", "-il", path, "-out", path, "uint8", "-ram",str(ram), "-exp", "(im1b1==1)?100:(im1b1==2)?205:255"])    

def format_SEB_VEC_values(path):
    table = op.splitext(op.basename(path))[0]
    call(["ogrinfo", path, "-sql", "ALTER TABLE "+table+" ADD COLUMN type varchar(15)"]) 
    call(["ogrinfo", path, "-dialect", "SQLite", "-sql", "UPDATE '"+table+"' SET DN=100, type='snow' WHERE DN=1"])
    call(["ogrinfo", path, "-dialect", "SQLite", "-sql", "UPDATE '"+table+"' SET DN=205, type='cloud' WHERE DN=2"])
    call(["ogrinfo", path, "-dialect", "SQLite", "-sql", "UPDATE '"+table+"' SET DN=255, type='no data' WHERE DN != 100 AND DN != 205"])
        