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
import os
import os.path as op
import json

#Custom C++ lib to compute histograms
import histo_utils_ext


def showHelp():
  print "This script is used to compute snow mask using OTB applications"
  print "Usage: s2snow.py param.json"

def polygonize(input_img,input_mask,output_vec):
    #Gdal polygonize
    call(["gdal_polygonize.py",input_img,"-f","ESRI Shapefile","-mask",input_mask,output_vec])

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
    #Parse Inputs 
    img=str(data["inputs"]["image"])
    dem=str(data["inputs"]["dem"])
    cloud_init=str(data["inputs"]["cloud_mask"])

    #Build image filenames
    redBand_path=op.join(path_tmp,"red.tif")
    ndsi_pass1_path=op.join(path_tmp,"pass1.tif")
    
    #parse cloud mask parameters
    rf=data["cloud_mask"]["rf"]
    rRed_darkcloud=data["cloud_mask"]["rRed_darkcloud"]
    rRed_backtocloud=data["cloud_mask"]["rRed_backtocloud"]
    
    #Pass -1 : generate custom cloud mask
    #Pass -1 extract redband
    call(["gdal_translate","-ot","Int16","-b","2",img,redBand_path])

    #resample red band using multiresolution pyramid
    call(["otbcli_MultiResolutionPyramid","-in",redBand_path,"-out",op.join(path_tmp,"red_warped.tif"),"int16","-sfactor",str(rf)])

    #oversample red band nn
    call(["otbcli_RigidTransformResample","-in",op.join(path_tmp,"red_warped_1.tif"),"-out",op.join(path_tmp,"red_nn.tif"),"int16","-transform.type.id.scalex",str(rf),"-transform.type.id.scaley",str(rf),"-interpolator","nn"])
    
    #Extract shadow mask
    condition_shadow= "(im1b1>0 and im2b1>" + str(rRed_darkcloud) + ") or (im1b1 >= " + str(shadow_value) + ")"
    call(["otbcli_BandMath","-il",cloud_init,op.join(path_tmp,"red_nn.tif"),"-out",cloud_refine,"uint8","-ram",str(ram),"-exp",condition_shadow + "?1:0"])

    #Parse snow parameters
    dz=data["snow"]["dz"]
    ndsi_pass1=data["snow"]["ndsi_pass1"]
    rRed_pass1=data["snow"]["rRed_pass1"]
    ndsi_pass2=data["snow"]["ndsi_pass2"]
    rRed_pass2=data["snow"]["rRed_pass2"]
    fsnow_lim=data["snow"]["fsnow_lim"]
    fsnow_total_lim=data["snow"]["fsnow_total_lim"]

    #Pass1 : NDSI threshold
    condition_pass1= "(im2b1!=1 and ((im1b1-im1b4)/(im1b1+im1b4))>"+ str(ndsi_pass1) + " and im1b2> " + str(rRed_pass1) + ")"
    call(["otbcli_BandMath","-il",img,cloud_refine,"-out",ndsi_pass1_path,"uint8","-ram",str(ram),"-exp",condition_pass1 + "?1:0"])


    #Update the cloud mask (again)
    condition_cloud_pass1= "(im1b1==1 or (im2b1!=1 and im3b1==1 and im4b1> " + str(rRed_backtocloud) + "))"
    call(["otbcli_BandMath","-il",cloud_refine,ndsi_pass1_path,cloud_init,redBand_path,"-out",op.join(path_tmp,"cloud_pass1.tif"),"uint8","-ram",str(ram),"-exp",condition_cloud_pass1 + "?1:0"])


    #Pass 2: compute snow fraction
    nb_snow_pixels= histo_utils_ext.compute_snow_fraction(ndsi_pass1_path)
    print "Number of snow pixels ", nb_snow_pixels
    
    if (nb_snow_pixels > fsnow_total_lim):
      #Pass 2: determine the Zs elevation fraction (done by external c++ code)
      zs=histo_utils_ext.compute_zs(dem,ndsi_pass1_path,op.join(path_tmp,"cloud_pass1.tif"), dz, fsnow_lim) 
      #Print zs
      print "computed ZS:", zs
      #TODO plug the right elevation
      #zs=2719
      
      if (zs !=-1):
        #NDSI threshold again
        condition_pass2= "(im3b1 != 1) and (im2b1>" + str(zs) + ") and ((im1b1-im1b4)/(im1b1+im1b4) > " + str(ndsi_pass2) + ") and (im1b2>" + str(rRed_pass2) + ")"
        call(["otbcli_BandMath","-il",img,dem,cloud_refine,"-out",op.join(path_tmp,"pass2.tif"),"uint8","-ram",str(1024),"-exp",condition_pass2 + "?1:0"])

        #poligonize
        polygonize(op.join(path_tmp,"pass2.tif"),op.join(path_tmp,"pass2.tif"),op.join(path_tmp,"pass2_vec.shp"))

        #Fuse pass1 and pass2
        condition_pass3= "(im1b1 == 1 or im2b1 == 1)"
        call(["otbcli_BandMath","-il",ndsi_pass1_path,op.join(path_tmp,"pass2.tif"),"-out",op.join(path_tmp,"pass3.tif"),"uint8","-ram",str(ram),"-exp",condition_pass3 + "?1:0"])

        generic_snow_path=op.join(path_tmp,"pass3.tif")
      else:
        print "did not find zs!"
        generic_snow_path=ndsi_pass1_path
      
    else:
        generic_snow_path=ndsi_pass1_path
    
    #Gdal polygonize
    polygonize(generic_snow_path,generic_snow_path,op.join(path_tmp,"pass3_vec.shp"))

    #TODO Final update of the cloud mask
    condition_final= "(im2b1==1)?1:((im1b1==1) or ((im3b1>0) and (im4b1> " + str(rRed_backtocloud) + ")))?2:0"
 
    call(["otbcli_BandMath","-il",cloud_refine,generic_snow_path,cloud_init,redBand_path,"-out",op.join(path_tmp,"final_mask.tif"),"uint8","-ram",str(ram),"-exp",condition_final])

    #Gdal polygonize
    polygonize(op.join(path_tmp,"final_mask.tif"),op.join(path_tmp,"final_mask.tif"),op.join(path_tmp,"final_mask_vec.shp"))

if __name__ == "__main__":
  if len(sys.argv) < 1 :
    showHelp()
  else:
    main(sys.argv)



