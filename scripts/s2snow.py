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
import compute_zs_ext
 

def showHelp():
  print "This script is used to compute snow mask using OTB applications"
  print "Usage: s2snow.py INPUT_IMAGE INPUT_DEM OUTPUT_IMG"

def polygonize(input_img,output_vec):
    #Gdal polygonize
    call(["gdal_polygonize.py",input_img,"-f","ESRI Shapefile",output_vec])

#----------------- MAIN ---------------------------------------------------
def main(argv):
    img=argv[1]
    dem=argv[2]
    cloud_init=argv[3]
    
    path_tmp="/home/grizonnetm/data/Output-CES-Neige/"
    cloud_refine=op.join(path_tmp,"cloud_refine.tif")

    #Pass -1 : generate custom cloud mask
    #Pass -1 extract redband
    call(["gdal_translate","-ot","Int16","-b","2",img,op.join(path_tmp,"red.tif")])

    #Pass1 : resample red band
    call(["gdalwarp","-r","bilinear","-tr",str(200),str(200),op.join(path_tmp,"red.tif"),op.join(path_tmp,"red_warped.tif")])

    #Pass2 : oversample red band nn
    call(["gdalwarp","-r","near","-tr",str(20),str(20),op.join(path_tmp,"red_warped.tif"),op.join(path_tmp,"red_nn.tif")])
    
    #Need to extract shadow mask
    condition_shadow= "(im1b1>0 and im2b1>500) or (im1b1 >= 64)"
    call(["otbcli_BandMath","-il",cloud_init,op.join(path_tmp,"red_nn.tif"),"-out",cloud_refine,"uint8","-ram",str(1024),"-exp",condition_shadow + "?1:0"])


    #Pass1 : NDSI threshold
    condition_pass1= "(im2b1!=1 and ((im1b1-im1b4)/(im1b1+im1b4))>0.4 and im1b2>200)"
    call(["otbcli_BandMath","-il",img,cloud_refine,"-out",op.join(path_tmp,"pass1.tif"),"uint8","-ram",str(1024),"-exp",condition_pass1 + "?1:0"])

    #TODO here we need to update again the could mask
    #TODO: determine the Zs elevation fraction (done by external c++ code)
    zs=compute_zs_ext.compute_zs(dem,op.join(path_tmp,"pass1.tif"),cloud_refine) 

    #trying to get zs
    print "computed ZS:", zs

    #Pass2
    condition_pass2= "(im3b1 != 1 and im2b1>" + str(zs) + " and ((im1b1-im1b4)/(im1b1+im1b4))>0.15 and im1b2>120)"
    call(["otbcli_BandMath","-il",img,dem,cloud_refine,"-out",op.join(path_tmp,"pass2.tif"),"uint8","-ram",str(1024),"-exp",condition_pass2 + "?1:0"])

    #poligonize
    polygonize(op.join(path_tmp,"pass2.tif"),op.join(path_tmp,"pass2_vec.shp"))

    #Fuse pass1 and pass2
    condition_pass3= "(im1b1 == 1 or im2b1 == 1)"
    call(["otbcli_BandMath","-il",op.join(path_tmp,"pass1.tif"),op.join(path_tmp,"pass2.tif"),"-out",op.join(path_tmp,"pass3.tif"),"uint8","-ram",str(1024),"-exp",condition_pass3 + "?1:0"])

    #Gdal polygonize
    polygonize(op.join(path_tmp,"pass3.tif"),op.join(path_tmp,"pass3_vec.shp"))

    #TODO Final update of the cloud mask
if __name__ == "__main__":
  if len(sys.argv) < 3 :
    showHelp()
  else:
    main(sys.argv)



