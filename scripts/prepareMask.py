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

def showHelp():
  print "This script is used to compute the derived mask for snow coverture computation"
  print "Usage: prepareMask.py INPUT_IMAGE INPUT_CLOUD_MASK OUTPUT_MASK"


#----------------- MAIN ---------------------------------------------------
def main(argv):
    img=argv[1]
    cloud=argv[2]
    output_img=argv[3]
    path_tmp="/home/grizonnetm/temporary"
    
    #Pass -1 extract redband
    call(["gdal_translate","-ot","Int16","-b","2",img,op.join(path_tmp,"red.tif")])

    #Pass1 : resample red band
    call(["gdalwarp","-r","bilinear","-ts",str(1000/8),str(1000/8),op.join(path_tmp,"red.tif"),op.join(path_tmp,"red_warped.tif")])

    #Pass2 : oversample red band
    call(["gdalwarp","-r","near","-ts",str(1000),str(1000),op.join(path_tmp,"red_warped.tif"),op.join(path_tmp,"red_nn.tif")])
    
    #Need to extract shadow mask
    condition_shadow= "(im1b1>0 and im2b1>500) or (im1b1 >= 64)"
    call(["otbcli_BandMath","-il",cloud,op.join(path_tmp,"red_nn.tif"),"-out",output_img,"uint8","-ram",str(1024),"-exp",condition_shadow + "?1:0"])

if __name__ == "__main__":
  if len(sys.argv) < 3 :
    showHelp()
  else:
    main(sys.argv)



