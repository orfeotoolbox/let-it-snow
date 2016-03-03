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

#TODO add qum
#fixme separate names and values formating
def format_ESA(snow_detector):
    version = snow_detector.version
    path_img = snow_detector.img
    pout = snow_detector.path_tmp
    xmltemplate = snow_detector.xmltemplate
    mode = snow_detector.mode
    zs = snow_detector.zs
    ram = snow_detector.ram
   
    #ID corresponding to the parent folder of the img
    productID = op.basename(op.abspath(op.join(path_img, os.pardir)))
    date = datetime.datetime.now()
    str_date = str(date.year)+str(date.month)+str(date.day)
    ext = "tif"
    str_final_mask = productID+"_"+str(version)+"_SEB_"+str_date+"."+ext 
    final_mask=op.join(pout, str_final_mask)

    os.rename(op.join(pout, "final_mask.tif"), final_mask)
    format_SEB_values(final_mask, ram)

    str_final_mask_vec_shp=""
    for f in glob.glob(op.join(pout, "final_mask_vec.*")):
        extension = op.splitext(f)[1]
        str_final_mask_vec = productID+"_"+str(version)+"_SEB_VEC_"+str_date+extension
        final_mask_vec = op.join(pout, str_final_mask_vec) 
        os.rename(f, final_mask_vec)
        if extension == ".dbf":
            format_SEB_VEC_values(final_mask_vec)
            if extension == ".shp":
                str_final_mask_vec_shp = final_mask_vec
                
    #copyfile(xmltemplate, "metadata.xml")
    tree = etree.parse(xmltemplate)
    root = tree.getroot()
    root.find('metadataFile').find('generationDateOfMetadatafile').text = str(datetime.datetime.now())
    root.find('link').find('snowExtentBinaryFile').text = final_mask 
    root.find('link').find('snowExtentBinaryVectorFile').text = str_final_mask_vec_shp
    root.find('processingInfo').find('softwareVersion').text = str(version)
    root.find('productInfo').find('productID').text = productID
    root.find('productInfo').find('mode').text = mode
    root.find('productInfo').find('ZS').text = str(zs)
    ds = gdal.Open(final_mask)
    prj = ds.GetProjection()
    root.find('mapProjection').text = str(prj)
    tree.write(op.join(pout, "metadata.xml"))
    

def format_SEB_values(final_mask_path, ram):
    call(["otbcli_BandMath", "-il", final_mask_path, "-out", final_mask_path, "uint8", "-ram",str(ram), "-exp", "(im1b1==1)?100:(im1b1==2)?205:255"])    

def format_SEB_VEC_values(final_mask_vec_path):
    table = op.splitext(op.basename(final_mask_vec_path))[0]
    call(["ogrinfo", final_mask_vec_path, "-sql", "ALTER TABLE "+table+" ADD COLUMN type varchar(15)"]) 
    call(["ogrinfo", final_mask_vec_path, "-dialect", "SQLite", "-sql", "UPDATE '"+table+"' SET DN=100, type='snow' WHERE DN=1"])
    call(["ogrinfo", final_mask_vec_path, "-dialect", "SQLite", "-sql", "UPDATE '"+table+"' SET DN=205, type='cloud' WHERE DN=2"])
    call(["ogrinfo", final_mask_vec_path, "-dialect", "SQLite", "-sql", "UPDATE '"+table+"' SET DN=255, type='no data' WHERE DN != 100 AND DN != 205"])
        
