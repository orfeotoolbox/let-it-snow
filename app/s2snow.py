#!/usr/bin/python
#coding=utf8
#=========================================================================
#
#  Program:   lis
#  Language:  Python
#
#  Copyright (c) Simon Gascoin
#  Copyright (c) Manuel Grizonnet
#
#  See lis-copyright.txt for details.
#
#  This software is distributed WITHOUT ANY WARRANTY; without even
#  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.  See the above copyright notices for more information.
#
#=========================================================================

import sys
from subprocess import call
import glob
import os
import os.path as op
import json
import gdal
from gdalconst import *
import glob

# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

#Internal C++ lib to compute histograms and minimum elevation threshold (step 2)
import histo_utils_ext

def showHelp():
    """Show help of the s2snow script"""
    print "This script is used to compute snow mask using OTB applications on Spot/LandSat/Sentinel-2 products from theia platform"
    print "Usage: s2snow.py param.json"

def polygonize(input_img,input_mask,output_vec):
    """Helper function to polygonize raster mask using gdal polygonize"""
    call(["gdal_polygonize.py",input_img,"-f","ESRI Shapefile","-mask",input_mask,output_vec])

def quicklook_RGB(input_img,output_img, nRed, nGreen, nSWIR):
    """make a RGB quicklook to highlight the snow cover
     
    input_img: multispectral Level 2 SPOT-4 (GTiff), output_img: false color
    composite RGB image (GTiff).nRed,nGreen,nSWIR are index of red, green and
    SWIR in in put images.

    """
    call(["gdal_translate","-co","PHOTOMETRIC=RGB","-scale","0","300","-ot","Byte","-b",str(nSWIR),"-b",str(nRed),"-b",str(nGreen),input_img,output_img])

def burn_polygons_edges(input_img,input_vec):
    """burn polygon borders onto an image with the following symbology:
     
    - cloud and cloud shadows: green
    - snow: magenta
    - convert mask polygons to lines

    """
    tmp_line="tmp_line"
    call(["ogr2ogr","-overwrite","-nlt","MULTILINESTRING",tmp_line+".shp",input_vec])
    # 2) rasterize cloud and cloud shadows polygon borders in green
    call(["gdal_rasterize","-b","1","-b","2","-b","3","-burn","0","-burn","255","-burn","0","-where","DN=\"2\"","-l","tmp_line",tmp_line+".shp",input_img])
    # 3) rasterize snow polygon borders in magenta
    call(["gdal_rasterize","-b","1","-b","2","-b","3","-burn","255","-burn","0","-burn","255","-where","DN=\"1\"","-l","tmp_line",tmp_line+".shp",input_img])
    # 4) remove tmp_line files
    call(["rm"]+glob.glob(tmp_line+"*"))

#----------------- MAIN ---------------------------------------------------
def main(argv):
    """ main script of snow extraction procedure"""

    json_file=argv[1]

    #load json_file from json files
    with open(json_file) as json_data_file:
      data = json.load(json_data_file)

    #Parse general parameters in json file
    path_tmp=str(data["general"]["pout"])
    cloud_refine=op.join(path_tmp,"cloud_refine.tif")
    shadow_value=data["general"]["shadow_value"]
    ram=data["general"]["ram"]
    
    mode=data["general"]["mode"]
    generate_vector=data["general"]["generate_vector"]

    #Parse input parameters
    img=str(data["inputs"]["image"])
    dem=str(data["inputs"]["dem"])
    cloud_init=str(data["inputs"]["cloud_mask"])

    #Build image path
    redBand_path=op.join(path_tmp,"red.tif")
    ndsi_pass1_path=op.join(path_tmp,"pass1.tif")
    
    if mode == "spot4":
      nGreen=1 # Index of green band
      nSWIR=4 # Index of SWIR band (1 to 3 µm) = band 11 (1.6 µm) in S2
      nRed=2 # Index of red band
      nodata=-10000 # no-data value
    elif mode == "landsat":
      nGreen=3
      nSWIR=6
      nRed=4
      nodata=-10000
    elif mode == "s2":
      #Handle Sentinel-2 case here. Sentinel-2 images are in 2 separates tif. R1
      #(green/red) at 10 meters and R2 (swir) at 20 meters. Need to extract each
      #band separately and resample green/red to 20 meters. 
      
      #Index of bands in R1 and R2 respectively
      nGreen=2
      nSWIR=5
      nRed=3
      nodata=-10000

      if not os.path.isdir(img):
        sys.exit("Sentinel-2 image path must be a directory!")

      #Build sentinel-2 image product path using Level2-a theia product
      #specification. Using FRE images to get slope correction products.
      s2_r1_img_path=glob.glob(op.join(img,"*FRE_R1*.TIF"))
      s2_r2_img_path=glob.glob(op.join(img,"*FRE_R2*.TIF"))

      if not s2_r1_img_path:
        sys.exit("No R1 S2 image found in Sentinel-2 directory.")

      if not s2_r2_img_path:
        sys.exit("No R2 S2 image found in Sentinel-2 directory.")

      #Build in path for extracted and resampled (20 merters) green band 
      greenBand_path=op.join(path_tmp,"green_s2.tif")
      greenBand_resample_path=op.join(path_tmp,"s2_green_resample.tif")

      #Build in path for extracted and resampled (20 merters) green band 
      redBand_path=op.join(path_tmp,"red_s2.tif")
      redBand_resample_path=op.join(path_tmp,"s2_red_resample.tif")

      #Path for swir band (already at 20 meters)
      swirBand_path=op.join(path_tmp,"swir_s2.tif")
      
      #Extract green bands and resample to 20 meters
      #FIXME Use multi resolution pyramid application or new resampling filter fontribute by J. Michel hear
      call(["gdal_translate","-ot","Int16","-b",str(nGreen),s2_r1_img_path[0],greenBand_path])
      call(["gdalwarp","-r","cubicspline","-tr","20","-20",greenBand_path,greenBand_resample_path])

      #Extract red bands and sample to 20 meters
      #FIXME Use multi resolution pyramid application or new resampling filter fontribute by J. Michel hear
      call(["gdal_translate","-ot","Int16","-b",str(nRed),s2_r1_img_path[0],redBand_path])
      call(["gdalwarp","-r","cubicspline","-tr","20","-20",redBand_path,redBand_resample_path])

      #Extract SWIR
      call(["gdal_translate","-ot","Int16","-b",str(nSWIR),s2_r2_img_path[0],swirBand_path])

      #Concatenate all bands in a single image
      concat_s2=op.join(path_tmp,"concat_s2.tif")
      call(["otbcli_ConcatenateImages","-il",greenBand_resample_path,redBand_resample_path,swirBand_path,"-out",concat_s2,"int16","-ram",str(ram)])

      #img variable is used later to compute snow mask
      img=concat_s2
      redBand_path=op.join(path_tmp,"red.tif")
      
      #Set generic band index for Sentinel-2
      nGreen=1
      nRed=2
      nSWIR=3
    else:
      sys.exit("Supported modes are spot4,landsat and s2.")
    
    
    #parse cloud mask parameters in json_file
    rf=data["cloud_mask"]["rf"]
    rRed_darkcloud=data["cloud_mask"]["rRed_darkcloud"]
    rRed_backtocloud=data["cloud_mask"]["rRed_backtocloud"]
    
    #Build gdal option to generate maks of 1 byte using otb extended filename
    #syntax
    gdal_opt="?&gdal:co:NBITS=1&gdal:co:COMPRESS=DEFLATE"
    #Build gdal option to generate maks of 2 bytes using otb extended filename
    #syntax
    gdal_opt_2b="?&gdal:co:NBITS=2&gdal:co:COMPRESS=DEFLATE"

    #Pass -1 : generate custom cloud mask
    #TODO: extract pass -1 in a custom function

    #Pass -1: Extract red band
    call(["gdal_translate","-ot","Int16","-b",str(nRed),img,redBand_path])

    dataset = gdal.Open( redBand_path, GA_ReadOnly )
    
    xSize=dataset.RasterXSize
    ySize=dataset.RasterYSize
    
    #Get geotransform to retrieve resolution
    geotransform = dataset.GetGeoTransform() 

    #resample red band using multiresolution pyramid
    #call(["otbcli_MultiResolutionPyramid","-in",redBand_path,"-out",op.join(path_tmp,"red_warped.tif"),"int16","-sfactor",str(rf)])
    call(["gdalwarp","-r","bilinear","-ts",str(xSize/rf),str(ySize/rf),redBand_path,op.join(path_tmp,"red_coarse.tif")])

    #Resample red band nn
    #FIXME: use MACCS resampling filter contribute by J. Michel here
    call(["gdalwarp","-r","near","-ts",str(xSize),str(ySize),op.join(path_tmp,"red_coarse.tif"),op.join(path_tmp,"red_nn.tif")])
    
    #edit result to set the resolution to the input image resolution
    #TODO need to find a better solution and also guess the input spacing (using maccs resampling filter)
    call(["gdal_edit.py","-tr",str(geotransform[1]),str(geotransform[5]),op.join(path_tmp,"red_nn.tif")])
    
    #Extract shadow mask
    condition_shadow= "(im1b1>0 and im2b1>" + str(rRed_darkcloud) + ") or (im1b1 >= " + str(shadow_value) + ")"
    call(["otbcli_BandMath","-il",cloud_init,op.join(path_tmp,"red_nn.tif"),"-out",cloud_refine+gdal_opt,"uint8","-ram",str(ram),"-exp",condition_shadow + "?1:0"])

    #Parse snow parameters in json_file
    dz=data["snow"]["dz"]
    ndsi_pass1=data["snow"]["ndsi_pass1"]
    rRed_pass1=data["snow"]["rRed_pass1"]
    ndsi_pass2=data["snow"]["ndsi_pass2"]
    rRed_pass2=data["snow"]["rRed_pass2"]
    fsnow_lim=data["snow"]["fsnow_lim"]
    fsnow_total_lim=data["snow"]["fsnow_total_lim"]

    #Pass1 : NDSI threshold
    ndsi_formula= "(im1b"+str(nGreen)+"-im1b"+str(nSWIR)+")/(im1b"+str(nGreen)+"+im1b"+str(nSWIR)+")"
    print "ndsi formula: ",ndsi_formula
    
    #Use 255 not 1 here because of bad handling of 1 byte tiff by otb)
    #FIXME
    condition_pass1= "(im2b1!=255 and ("+ndsi_formula+")>"+ str(ndsi_pass1) + " and im1b"+str(nRed)+"> " + str(rRed_pass1) + ")"
    call(["otbcli_BandMath","-il",img,cloud_refine,"-out",ndsi_pass1_path+gdal_opt,"uint8","-ram",str(ram),"-exp",condition_pass1 + "?1:0"])
    
    #Update the cloud mask (again)
    #Use 255 not 1 here because of bad handling of 1 byte tiff by otb)
    #FIXME
    condition_cloud_pass1= "(im1b1==255 or (im2b1!=255 and im3b1==1 and im4b1> " + str(rRed_backtocloud) + "))"
    call(["otbcli_BandMath","-il",cloud_refine,ndsi_pass1_path,cloud_init,redBand_path,"-out",op.join(path_tmp,"cloud_pass1.tif")+gdal_opt,"uint8","-ram",str(ram),"-exp",condition_cloud_pass1 + "?1:0"])

    #Pass 2: compute snow fraction (c++)
    nb_snow_pixels= histo_utils_ext.compute_snow_fraction(ndsi_pass1_path)
    print "Number of snow pixels ", nb_snow_pixels
    
    if (nb_snow_pixels > fsnow_total_lim):
      #Pass 2: determine the Zs elevation fraction (c++)
      #Save histogram values for logging
      histo_log=op.join(path_tmp,"histogram.txt")
      #c++ function
      zs=histo_utils_ext.compute_zs_ng(dem,ndsi_pass1_path,op.join(path_tmp,"cloud_pass1.tif"), dz, fsnow_lim, histo_log) 
      
      print "computed ZS:", zs
      
      #Test zs value (-1 means that no zs elevation was found)
      if (zs !=-1):
        #NDSI threshold again
        #Use 255 not 1 here because of bad handling of 1 byte tiff by otb)
        #FIXME
        condition_pass2= "(im3b1 != 255) and (im2b1>" + str(zs) + ") and (" + ndsi_formula + "> " + str(ndsi_pass2) + ") and (im1b"+str(nRed)+">" + str(rRed_pass2) + ")"
        call(["otbcli_BandMath","-il",img,dem,cloud_refine,"-out",op.join(path_tmp,"pass2.tif")+gdal_opt,"uint8","-ram",str(1024),"-exp",condition_pass2 + "?1:0"])

	if generate_vector:
          #Generate polygons for pass2 (useful for quality check)
          #TODO 
          polygonize(op.join(path_tmp,"pass2.tif"),op.join(path_tmp,"pass2.tif"),op.join(path_tmp,"pass2_vec.shp"))

        #Fuse pass1 and pass2 (use 255 not 1 here because of bad handling of 1 byte tiff by otb)
        #FIXME
        condition_pass3= "(im1b1 == 255 or im2b1 == 255)"
        call(["otbcli_BandMath","-il",ndsi_pass1_path,op.join(path_tmp,"pass2.tif"),"-out",op.join(path_tmp,"pass3.tif")+gdal_opt,"uint8","-ram",str(ram),"-exp",condition_pass3 + "?1:0"])

        generic_snow_path=op.join(path_tmp,"pass3.tif")
      else:
        #No zs elevation found, take result of pass1 in the output product
        print "did not find zs, keep pass 1 result."
        generic_snow_path=ndsi_pass1_path
      
    else:
        generic_snow_path=ndsi_pass1_path
    
    if generate_vector:
      #Generate polygons for pass3 (useful for quality check)
      polygonize(generic_snow_path,generic_snow_path,op.join(path_tmp,"pass3_vec.shp"))

    # Final update of the cloud mask (use 255 not 1 here because of bad handling of 1 byte tiff by otb)
    condition_final= "(im2b1==255)?1:((im1b1==255) or ((im3b1>0) and (im4b1> " + str(rRed_backtocloud) + ")))?2:0"
 
    call(["otbcli_BandMath","-il",cloud_refine,generic_snow_path,cloud_init,redBand_path,"-out",op.join(path_tmp,"final_mask.tif")+gdal_opt_2b,"uint8","-ram",str(ram),"-exp",condition_final])

    #Gdal polygonize (needed to produce quicklook)
    #TODO: Study possible loss and issue with vectorization product
    polygonize(op.join(path_tmp,"final_mask.tif"),op.join(path_tmp,"final_mask.tif"),op.join(path_tmp,"final_mask_vec.shp"))

    #RGB quicklook (quality insurance)
    quicklook_RGB(img,op.join(path_tmp,"quicklook.tif"),nRed,nGreen,nSWIR)

    #Burn polygons edges on the quicklook
    #TODO add pass1 snow polygon in yellow
    burn_polygons_edges(op.join(path_tmp,"quicklook.tif"),op.join(path_tmp,"final_mask_vec.shp"))

if __name__ == "__main__":
  if len(sys.argv) != 2 :
    showHelp()
  else:
    main(sys.argv)



