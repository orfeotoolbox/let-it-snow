#!/usr/bin/python
#coding=utf8
#==========================================================================
#
#   Copyright Insight Software Consortium
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0.txt
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#
#==========================================================================*/
# 
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

#Custom C++ lib to compute histograms
import histo_utils_ext


def showHelp():
  print "This script is used to compute snow mask using OTB applications"
  print "Usage: s2snow.py param.json"

def polygonize(input_img,input_mask,output_vec):
    #Gdal polygonize
    call(["gdal_polygonize.py",input_img,"-f","ESRI Shapefile","-mask",input_mask,output_vec])

def quicklook_RGB(input_img,output_img, nRed, nGreen, nMIR):
    #make a RGB quicklook to highlight the snow cover  
    #input_img: multispectral Level 2 SPOT-4 (GTiff), output_img: false color composite RGB image (GTiff)
    call(["gdal_translate","-co","PHOTOMETRIC=RGB","-scale","0","300","-ot","Byte","-b",str(nMIR),"-b",str(nRed),"-b",str(nGreen),input_img,output_img])

def burn_polygons_edges(input_img,input_vec):
    #burn polygon borders onto an image with the following symbology: 
    # - cloud and cloud shadows: green
    # - snow: magenta
    # 1) convert mask polygons to lines
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
    parameters=argv[1]

    #load parameters from json files
    with open(parameters) as json_data_file:
      data = json.load(json_data_file)
    #pprint(data)

    #Parse general parameters
    path_tmp=str(data["general"]["pout"])
    cloud_refine=op.join(path_tmp,"cloud_refine.tif")
    shadow_value=data["general"]["shadow_value"]
    ram=data["general"]["ram"]
    
    mode=data["general"]["mode"]
    generate_vector=data["general"]["generate_vector"]

    #Parse Inputs 
    img=str(data["inputs"]["image"])
    dem=str(data["inputs"]["dem"])
    cloud_init=str(data["inputs"]["cloud_mask"])

    #Build image filenames
    redBand_path=op.join(path_tmp,"red.tif")
    ndsi_pass1_path=op.join(path_tmp,"pass1.tif")
    
    if mode == "spot4":
      nGreen=1 # Index of green band
      nMIR=4 # Index of SWIR band (1 to 3 µm) = band 11 (1.6 µm) in S2
      nRed=2 # Index of red band
      nodata=-10000 # no-data value
    elif mode == "landsat":
      nGreen=3
      nMIR=6
      nRed=4
      nodata=-10000
    elif mode == "s2":
      #Number of bands in R1 and R2 respectively
      nGreen=2
      nMIR=5
      nRed=3
      nodata=-10000

      if not os.path.isdir(img):
        sys.exit("Sentinel-2 image path must be a directory!")
      
      s2_r1_img_path=glob.glob(op.join(img,"*FRE_R1*.TIF"))
      s2_r2_img_path=glob.glob(op.join(img,"*FRE_R2*.TIF"))

      if not s2_r1_img_path:
        sys.exit("No R1 S2 image found.")

      if not s2_r2_img_path:
        sys.exit("No R2 S2 image found.")
      
      greenBand_path=op.join(path_tmp,"green_s2.tif")
      greenBand_resample_path=op.join(path_tmp,"s2_green_resample.tif")

      redBand_path=op.join(path_tmp,"red_s2.tif")
      redBand_resample_path=op.join(path_tmp,"s2_red_resample.tif")

      mirBand_path=op.join(path_tmp,"mir_s2.tif")
      #mirBand_resample_path=op.join(path_tmp,"s2_mir_resample.tif")
      
      #print "s2_r1_img_path ", s2_r1_img_path[0]
      #print "s2_r2_img_path ", s2_r2_img_path[0]
      #Extract green bands and sample to 20 meters
      call(["gdal_translate","-ot","Int16","-b",str(nGreen),s2_r1_img_path[0],greenBand_path])
      call(["gdalwarp","-r","cubicspline","-tr","20","-20",greenBand_path,greenBand_resample_path])

      #Extract red bands and sample to 20 meters
      call(["gdal_translate","-ot","Int16","-b",str(nRed),s2_r1_img_path[0],redBand_path])
      call(["gdalwarp","-r","cubicspline","-tr","20","-20",redBand_path,redBand_resample_path])

      #Extract MIR
      call(["gdal_translate","-ot","Int16","-b",str(nMIR),s2_r2_img_path[0],mirBand_path])

      #Concatenate all bands in a single image
      concat_s2=op.join(path_tmp,"concat_s2.tif")
      call(["otbcli_ConcatenateImages","-il",greenBand_resample_path,redBand_resample_path,mirBand_path,"-out",concat_s2,"int16","-ram",str(ram)])

      #Concat in img variable
      img=concat_s2
      redBand_path=op.join(path_tmp,"red.tif")
      
      nGreen=1
      nRed=2
      nMIR=3
    else:
      sys.exit("Supported sensors:  spot4, landsat, s2")
    
    
    #parse cloud mask parameters
    rf=data["cloud_mask"]["rf"]
    rRed_darkcloud=data["cloud_mask"]["rRed_darkcloud"]
    rRed_backtocloud=data["cloud_mask"]["rRed_backtocloud"]
    
    #Build gdal option to generate maks of 1 byte
    gdal_opt="?&gdal:co:NBITS=1&gdal:co:COMPRESS=DEFLATE"
    #Build gdal option to generate maks of 2 bytes
    gdal_opt2="?&gdal:co:NBITS=2&gdal:co:COMPRESS=DEFLATE"

    
    #Pass -1 : generate custom cloud mask
    #Pass -1 extract redband
    print "img s2 ", img
    
    call(["gdal_translate","-ot","Int16","-b",str(nRed),img,redBand_path])

    dataset = gdal.Open( redBand_path, GA_ReadOnly )
    
    xSize=dataset.RasterXSize
    ySize=dataset.RasterYSize
    
    #Get geotransform to retrieve resolution
    geotransform = dataset.GetGeoTransform() 

    #resample red band using multiresolution pyramid
    #call(["otbcli_MultiResolutionPyramid","-in",redBand_path,"-out",op.join(path_tmp,"red_warped.tif"),"int16","-sfactor",str(rf)])
    call(["gdalwarp","-r","bilinear","-ts",str(xSize/rf),str(ySize/rf),redBand_path,op.join(path_tmp,"red_coarse.tif")])

    #oversample red band nn
    #call(["otbcli_RigidTransformResample","-in",op.join(path_tmp,"red_warped_1.tif"),"-out",op.join(path_tmp,"red_nn.tif"),"int16","-transform.type.id.scalex",str(rf),"-transform.type.id.scaley",str(rf),"-interpolator","nn"])
    call(["gdalwarp","-r","near","-ts",str(xSize),str(ySize),op.join(path_tmp,"red_coarse.tif"),op.join(path_tmp,"red_nn.tif")])
    
    #edit result to set the resolution to the input image resolution
    #TODO need to find a better solution and also guess the input spacing
    call(["/mnt/data/home/otbtest/OTB/SuperBuild/OTB/GDAL/build/swig/python/scripts/gdal_edit.py","-tr",str(geotransform[1]),str(geotransform[5]),op.join(path_tmp,"red_nn.tif")])
    #call(["gdal_edit.py","-tr",str(geotransform[1]),str(geotransform[5]),op.join(path_tmp,"red_nn.tif")])
    #Extract shadow mask
    condition_shadow= "(im1b1>0 and im2b1>" + str(rRed_darkcloud) + ") or (im1b1 >= " + str(shadow_value) + ")"
    call(["otbcli_BandMath","-il",cloud_init,op.join(path_tmp,"red_nn.tif"),"-out",cloud_refine+gdal_opt,"uint8","-ram",str(ram),"-exp",condition_shadow + "?1:0"])

    #Parse snow parameters
    dz=data["snow"]["dz"]
    ndsi_pass1=data["snow"]["ndsi_pass1"]
    rRed_pass1=data["snow"]["rRed_pass1"]
    ndsi_pass2=data["snow"]["ndsi_pass2"]
    rRed_pass2=data["snow"]["rRed_pass2"]
    fsnow_lim=data["snow"]["fsnow_lim"]
    fsnow_total_lim=data["snow"]["fsnow_total_lim"]

    #Pass1 : NDSI threshold

    ndsi_formula= "(im1b"+str(nGreen)+"-im1b"+str(nMIR)+")/(im1b"+str(nGreen)+"+im1b"+str(nMIR)+")"
    print "ndsi formula: ",ndsi_formula
    
    condition_pass1= "(im2b1!=255 and ("+ndsi_formula+")>"+ str(ndsi_pass1) + " and im1b"+str(nRed)+"> " + str(rRed_pass1) + ")"
    call(["otbcli_BandMath","-il",img,cloud_refine,"-out",ndsi_pass1_path+gdal_opt,"uint8","-ram",str(ram),"-exp",condition_pass1 + "?1:0"])
    
    #Update the cloud mask (again)
    condition_cloud_pass1= "(im1b1==255 or (im2b1!=255 and im3b1==1 and im4b1> " + str(rRed_backtocloud) + "))"
    call(["otbcli_BandMath","-il",cloud_refine,ndsi_pass1_path,cloud_init,redBand_path,"-out",op.join(path_tmp,"cloud_pass1.tif")+gdal_opt,"uint8","-ram",str(ram),"-exp",condition_cloud_pass1 + "?1:0"])


    #Pass 2: compute snow fraction
    nb_snow_pixels= histo_utils_ext.compute_snow_fraction(ndsi_pass1_path)
    print "Number of snow pixels ", nb_snow_pixels
    
    if (nb_snow_pixels > fsnow_total_lim):
      #Pass 2: determine the Zs elevation fraction (done by external c++ code)
      histo_log=op.join(path_tmp,"histogram.txt")

      zs=histo_utils_ext.compute_zs_ng(dem,ndsi_pass1_path,op.join(path_tmp,"cloud_pass1.tif"), dz, fsnow_lim, histo_log) 
      #Print zs
      print "computed ZS:", zs
      #TODO plug the right elevation
      #zs=2719
      
      if (zs !=-1):
        #NDSI threshold again
        condition_pass2= "(im3b1 != 255) and (im2b1>" + str(zs) + ") and (" + ndsi_formula + "> " + str(ndsi_pass2) + ") and (im1b"+str(nRed)+">" + str(rRed_pass2) + ")"
        call(["otbcli_BandMath","-il",img,dem,cloud_refine,"-out",op.join(path_tmp,"pass2.tif")+gdal_opt,"uint8","-ram",str(1024),"-exp",condition_pass2 + "?1:0"])

	if generate_vector:
          #polygonize
          polygonize(op.join(path_tmp,"pass2.tif"),op.join(path_tmp,"pass2.tif"),op.join(path_tmp,"pass2_vec.shp"))

        #Fuse pass1 and pass2
        condition_pass3= "(im1b1 == 255 or im2b1 == 255)"
        call(["otbcli_BandMath","-il",ndsi_pass1_path,op.join(path_tmp,"pass2.tif"),"-out",op.join(path_tmp,"pass3.tif")+gdal_opt,"uint8","-ram",str(ram),"-exp",condition_pass3 + "?1:0"])

        generic_snow_path=op.join(path_tmp,"pass3.tif")
      else:
        print "did not find zs!"
        generic_snow_path=ndsi_pass1_path
      
    else:
        generic_snow_path=ndsi_pass1_path
    
    if generate_vector:
      #Gdal polygonize
      polygonize(generic_snow_path,generic_snow_path,op.join(path_tmp,"pass3_vec.shp"))

    #TODO Final update of the cloud mask
    condition_final= "(im2b1==255)?1:((im1b1==255) or ((im3b1>0) and (im4b1> " + str(rRed_backtocloud) + ")))?2:0"
 
    call(["otbcli_BandMath","-il",cloud_refine,generic_snow_path,cloud_init,redBand_path,"-out",op.join(path_tmp,"final_mask.tif")+gdal_opt2,"uint8","-ram",str(ram),"-exp",condition_final])

    #Gdal polygonize (needed to produce quicklook)
    polygonize(op.join(path_tmp,"final_mask.tif"),op.join(path_tmp,"final_mask.tif"),op.join(path_tmp,"final_mask_vec.shp"))

    #RGB quicklook
    quicklook_RGB(img,op.join(path_tmp,"quicklook.tif"),nRed,nGreen,nMIR)

    #Burn polygons edges on the quicklook
    #TODO add pass1 snow polygon in yellow
    burn_polygons_edges(op.join(path_tmp,"quicklook.tif"),op.join(path_tmp,"final_mask_vec.shp"))


if __name__ == "__main__":
  if len(sys.argv) != 2 :
    showHelp()
  else:
    main(sys.argv)



