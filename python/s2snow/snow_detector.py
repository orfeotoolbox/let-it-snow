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

#Preprocessing an postprocessing script
import dem_builder
import format_output

VERSION="0.1"

#Build gdal option to generate maks of 1 byte using otb extended filename
#syntax
GDAL_OPT="?&gdal:co:NBITS=1&gdal:co:COMPRESS=DEFLATE"
#Build gdal option to generate maks of 2 bytes using otb extended filename
#syntax
GDAL_OPT_2B="?&gdal:co:NBITS=2&gdal:co:COMPRESS=DEFLATE"

#TODO add temporaty directory

def polygonize(input_img,input_mask,output_vec):
    """Helper function to polygonize raster mask using gdal polygonize"""
    call(["gdal_polygonize.py",input_img,"-f","ESRI Shapefile","-mask",input_mask,output_vec])

def quicklook_RGB(input_img,output_img, nRed, nGreen, nSWIR):
    """Make a RGB quicklook to highlight the snow cover
     
    input_img: multispectral Level 2 SPOT-4 (GTiff), output_img: false color
    composite RGB image (GTiff).nRed,nGreen,nSWIR are index of red, green and
    SWIR in in put images.

    """
    call(["gdal_translate","-co","PHOTOMETRIC=RGB","-scale","0","300","-ot","Byte","-b",str(nSWIR),"-b",str(nRed),"-b",str(nGreen),input_img,output_img])

def burn_polygons_edges(input_img,input_vec):
    """Burn polygon borders onto an image with the following symbology:
     
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

class snow_detector :
    def __init__(self, data):
        
        self.version = VERSION
        #Parse general parameters
        self.path_tmp=str(data["general"]["pout"])
        self.ram=data["general"]["ram"]
        self.mode=data["general"]["mode"]
        self.generate_vector=data["general"]["generate_vector"]
        self.do_preprocessing=data["general"]["preprocessing"]
        self.do_postprocessing=True
        self.do_quicklook=True
        self.shadow_value=data["general"]["shadow_value"]
        #Parse cloud data
        self.rf=data["cloud_mask"]["rf"]
        self.rRed_darkcloud=data["cloud_mask"]["rRed_darkcloud"]
        self.rRed_backtocloud=data["cloud_mask"]["rRed_backtocloud"]
        #Parse input parameters
        self.vrt=str(data["inputs"]["vrt"]) 
        self.img=str(data["inputs"]["image"])
        self.dem=str(data["inputs"]["dem"])
        self.xmltemplate = str(data["inputs"]["xml"])
        self.cloud_init=str(data["inputs"]["cloud_mask"])
        #Parse snow parameters
        self.dz=data["snow"]["dz"]
        self.ndsi_pass1=data["snow"]["ndsi_pass1"]
        self.rRed_pass1=data["snow"]["rRed_pass1"]
        self.ndsi_pass2=data["snow"]["ndsi_pass2"]
        self.rRed_pass2=data["snow"]["rRed_pass2"]
        self.fsnow_lim=data["snow"]["fsnow_lim"]
        self.fsnow_total_lim=data["snow"]["fsnow_total_lim"]
        #Build useful paths
        self.redBand_path=op.join(self.path_tmp,"red.tif")
        self.ndsi_pass1_path=op.join(self.path_tmp,"pass1.tif")
        self.cloud_refine=op.join(self.path_tmp,"cloud_refine.tif")
        
        #Set bands parameters
        self.nGreen=0
        self.nSWIR=0
        self.nRed=0 
        self.nodata=0
        if self.mode == "spot4":
            self.nGreen=1 # Index of green band
            self.nSWIR=4 # Index of SWIR band (1 to 3 µm) = band 11 (1.6 µm) in S2
            self.nRed=2 # Index of red band
            self.nodata=-10000 # no-data value
        elif self.mode == "landsat":
            self.nGreen=3
            self.nSWIR=6
            self.nRed=4 
            self.nodata=-10000
        elif self.mode == "s2":
            sentinel_2_preprocessing()
            #Set generic band index for Sentinel-2
            self.nGreen=1
            self.nRed=2
            self.nSWIR=3
        else:
            sys.exit("Supported modes are spot4,landsat and s2.")
    
    def detect_snow(self, nbPass):
        #External preprocessing
        if self.do_preprocessing: 
            preprocessing.build_dem(vrt, img, dem)
        
        if nbPass >= 0 :
            self.pass0()
        if nbPass >= 1 :
            self.pass1()
        if nbPass == 2 :
            self.pass2()
        
        if self.do_quicklook:
            #Gdal polygonize (needed to produce quicklook)
            #TODO: Study possible loss and issue with vectorization product
            polygonize(op.join(self.path_tmp,"final_mask.tif"),op.join(self.path_tmp,"final_mask.tif"),op.join(self.path_tmp,"final_mask_vec.shp"))

            #RGB quicklook (quality insurance)
            quicklook_RGB(self.img,op.join(self.path_tmp,"quicklook.tif"),self.nRed,self.nGreen,self.nSWIR)

            #Burn polygons edges on the quicklook
            #TODO add pass1 snow polygon in yellow
            burn_polygons_edges(op.join(self.path_tmp,"quicklook.tif"),op.join(self.path_tmp,"final_mask_vec.shp"))
    
        #External postprocessing
        if self.do_postprocessing:
            format_output.format_LIS(self) 

    def pass0(self):
        #Pass -1 : generate custom cloud mask
        #Extract red band
        call(["gdal_translate","-ot","Int16","-b",str(self.nRed),self.img,self.redBand_path])
        dataset = gdal.Open( self.redBand_path, GA_ReadOnly )
        
        xSize=dataset.RasterXSize
        ySize=dataset.RasterYSize
        
        #Get geotransform to retrieve resolution
        geotransform = dataset.GetGeoTransform() 
        
        #resample red band using multiresolution pyramid
        #call(["otbcli_MultiResolutionPyramid","-in",redBand_path,"-out",op.join(path_tmp,"red_warped.tif"),"int16","-sfactor",str(rf)])
        call(["gdalwarp","-r","bilinear","-ts",str(xSize/self.rf),str(ySize/self.rf),self.redBand_path,op.join(self.path_tmp,"red_coarse.tif")])
        
        #Resample red band nn
        #FIXME: use MACCS resampling filter contribute by J. Michel here
        call(["gdalwarp","-r","near","-ts",str(xSize),str(ySize),op.join(self.path_tmp,"red_coarse.tif"),op.join(self.path_tmp,"red_nn.tif")])
        
        #edit result to set the resolution to the input image resolution
        #TODO need to find a better solution and also guess the input spacing (using maccs resampling filter)
        call(["gdal_edit.py","-tr",str(geotransform[1]),str(geotransform[5]),op.join(self.path_tmp,"red_nn.tif")])
        
        #Extract shadow mask
        condition_shadow= "(im1b1>0 and im2b1>" + str(self.rRed_darkcloud) + ") or (im1b1 >= " + str(self.shadow_value) + ")"
        call(["otbcli_BandMath","-il",self.cloud_init,op.join(self.path_tmp,"red_nn.tif"),"-out",self.cloud_refine+GDAL_OPT,"uint8","-ram",str(self.ram),"-exp",condition_shadow + "?1:0"])

    def pass1(self):
        #Pass1 : NDSI threshold
        ndsi_formula= "(im1b"+str(self.nGreen)+"-im1b"+str(self.nSWIR)+")/(im1b"+str(self.nGreen)+"+im1b"+str(self.nSWIR)+")"
        print "ndsi formula: ",ndsi_formula
        
        #Use 255 not 1 here because of bad handling of 1 byte tiff by otb)
        #FIXME
        condition_pass1= "(im2b1!=255 and ("+ndsi_formula+")>"+ str(self.ndsi_pass1) + " and im1b"+str(self.nRed)+"> " + str(self.rRed_pass1) + ")"
        call(["otbcli_BandMath","-il",self.img,self.cloud_refine,"-out",self.ndsi_pass1_path+GDAL_OPT,"uint8","-ram",str(self.ram),"-exp",condition_pass1 + "?1:0"])
        
        #Update the cloud mask (again)
        #Use 255 not 1 here because of bad handling of 1 byte tiff by otb)
        #FIXME
        condition_cloud_pass1= "(im1b1==255 or (im2b1!=255 and im3b1==1 and im4b1> " + str(self.rRed_backtocloud) + "))"
        call(["otbcli_BandMath","-il",self.cloud_refine,self.ndsi_pass1_path,self.cloud_init,self.redBand_path,"-out",op.join(self.path_tmp,"cloud_pass1.tif")+GDAL_OPT,"uint8","-ram",str(self.ram),"-exp",condition_cloud_pass1 + "?1:0"])
        
    def pass2(self):
        ndsi_formula= "(im1b"+str(self.nGreen)+"-im1b"+str(self.nSWIR)+")/(im1b"+str(self.nGreen)+"+im1b"+str(self.nSWIR)+")"
        #Pass 2: compute snow fraction (c++)
        nb_snow_pixels = histo_utils_ext.compute_snow_fraction(self.ndsi_pass1_path)
        print "Number of snow pixels ", nb_snow_pixels
        
        if (nb_snow_pixels > self.fsnow_total_lim):
            #Pass 2: determine the Zs elevation fraction (c++)
            #Save histogram values for logging
            histo_log=op.join(self.path_tmp,"histogram.txt")
            #c++ function
            self.zs=histo_utils_ext.compute_zs_ng(self.dem,self.ndsi_pass1_path,op.join(self.path_tmp,"cloud_pass1.tif"), self.dz, self.fsnow_lim, histo_log) 
            
            print "computed ZS:", self.zs
            
            #Test zs value (-1 means that no zs elevation was found)
            if (self.zs !=-1):
                #NDSI threshold again
                #Use 255 not 1 here because of bad handling of 1 byte tiff by otb)
                #FIXME
                condition_pass2= "(im3b1 != 255) and (im2b1>" + str(self.zs) + ") and (" + ndsi_formula + "> " + str(self.ndsi_pass2) + ") and (im1b"+str(self.nRed)+">" + str(self.rRed_pass2) + ")"
                call(["otbcli_BandMath","-il",self.img,self.dem,self.cloud_refine,"-out",op.join(self.path_tmp,"pass2.tif")+GDAL_OPT,"uint8","-ram",str(1024),"-exp",condition_pass2 + "?1:0"])

                if self.generate_vector:
                    #Generate polygons for pass2 (useful for quality check)
                    #TODO 
                    polygonize(op.join(self.path_tmp,"pass2.tif"),op.join(self.path_tmp,"pass2.tif"),op.join(self.path_tmp,"pass2_vec.shp"))
                self.pass3()    
                generic_snow_path=op.join(self.path_tmp,"pass3.tif")
            else:
                #No zs elevation found, take result of pass1 in the output product
                print "did not find zs, keep pass 1 result."
                generic_snow_path=self.ndsi_pass1_path
                    
        else:
            generic_snow_path=self.ndsi_pass1_path
                    
        if self.generate_vector:
            #Generate polygons for pass3 (useful for quality check)
            polygonize(generic_snow_path,generic_snow_path,op.join(self.path_tmp,"pass3_vec.shp"))
            
        # Final update of the cloud mask (use 255 not 1 here because of bad handling of 1 byte tiff by otb)
        condition_final= "(im2b1==255)?1:((im1b1==255) or ((im3b1>0) and (im4b1> " + str(self.rRed_backtocloud) + ")))?2:0"
                        
        call(["otbcli_BandMath","-il",self.cloud_refine,generic_snow_path,self.cloud_init,self.redBand_path,"-out",op.join(self.path_tmp,"final_mask.tif")+GDAL_OPT_2B,"uint8","-ram",str(self.ram),"-exp",condition_final])
        
        call(["compute_snow_mask", op.join(self.path_tmp,"pass1.tif"), op.join(self.path_tmp,"pass2.tif"), op.join(self.path_tmp,"cloud_pass1.tif"),  op.join(self.path_tmp,"cloud_refine.tif"), op.join(self.path_tmp, "snow_all.tif")])
        
        dataset = gdal.Open(generic_snow_path, GA_ReadOnly)
        #assume that snow and coloud images are of the same size
        total_pixels=dataset.RasterXSize*dataset.RasterYSize
        print total_pixels
        
        self.snow_percent = float(histo_utils_ext.compute_snow_fraction(generic_snow_path) * 100)/total_pixels
        print "snow percent: " + str(self.snow_percent)
        # snow = cloud
        self.cloud_percent = float(histo_utils_ext.compute_snow_fraction(op.join(self.path_tmp,"cloud_refine.tif")) * 100)/total_pixels
        print "cloud percent: " + str(self.cloud_percent)

    def pass3(self):
        #Fuse pass1 and pass2 (use 255 not 1 here because of bad handling of 1 byte tiff by otb)
        #FIXME
        condition_pass3= "(im1b1 == 255 or im2b1 == 255)"
        call(["otbcli_BandMath","-il",self.ndsi_pass1_path,op.join(self.path_tmp,"pass2.tif"),"-out",op.join(self.path_tmp,"pass3.tif")+GDAL_OPT,"uint8","-ram",str(self.ram),"-exp",condition_pass3 + "?1:0"])

    def sentinel_2_preprocessing(self):
        #Handle Sentinel-2 case here. Sentinel-2 images are in 2 separates tif. R1
        #(green/red) at 10 meters and R2 (swir) at 20 meters. Need to extract each
        #band separately and resample green/red to 20 meters. 
        
        #Index of bands in R1 and R2 respectively
        nGreen=2
        nSWIR=5
        nRed=3
        nodata=-10000
           
        if not os.path.isdir(self.img):
            sys.exit("Sentinel-2 image path must be a directory!")

        #Build sentinel-2 image product path using Level2-a theia product
        #specification. Using FRE images to get slope correction products.
        s2_r1_img_path=glob.glob(op.join(self.img,"*FRE_R1*.TIF"))
        s2_r2_img_path=glob.glob(op.join(self.img,"*FRE_R2*.TIF"))
        
        if not s2_r1_img_path:
            sys.exit("No R1 S2 image found in Sentinel-2 directory.")
        
        if not s2_r2_img_path:
            sys.exit("No R2 S2 image found in Sentinel-2 directory.")
            
        #Build in path for extracted and resampled (20 merters) green band 
        greenBand_path=op.join(self.path_tmp,"green_s2.tif")
        greenBand_resample_path=op.join(self.path_tmp,"s2_green_resample.tif")
        
        #Build in path for extracted and resampled (20 merters) green band 
        redBand_path=op.join(self.path_tmp,"red_s2.tif")
        redBand_resample_path=op.join(self.path_tmp,"s2_red_resample.tif")
                        
        #Path for swir band (already at 20 meters)
        swirBand_path=op.join(self.path_tmp,"swir_s2.tif")
                        
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
        self.img=concat_s2
        self.redBand_path=op.join(path_tmp,"red.tif")