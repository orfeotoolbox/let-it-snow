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
import subprocess
import glob
import os
import os.path as op
import json
import gdal
from gdalconst import *
import multiprocessing
import numpy as np
import uuid
from shutil import copyfile

# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

#Internal C++ lib to compute histograms and minimum elevation threshold (step 2)
import histo_utils_ext

#Preprocessing an postprocessing script
import dem_builder
import format_output

VERSION="0.1"

#Build gdal option to generate maks of 1 byte using otb extended filename
#syntaxx
GDAL_OPT="?&gdal:co:NBITS=1&gdal:co:COMPRESS=DEFLATE"
#Build gdal option to generate maks of 2 bytes using otb extended filename
#syntax
GDAL_OPT_2B="?&gdal:co:NBITS=2&gdal:co:COMPRESS=DEFLATE"

# run subprocess and write to stdout and stderr
def call_subprocess(process_list):
	process = subprocess.Popen(process_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = process.communicate()
	print out
	sys.stderr.write(err)

def polygonize(input_img,input_mask,output_vec):
	"""Helper function to polygonize raster mask using gdal polygonize"""
	call_subprocess(["gdal_polygonize.py",input_img,"-f","ESRI Shapefile","-mask",input_mask,output_vec])

def composition_RGB(input_img,output_img):
	"""Make a RGB composition to highlight the snow cover
	 
	input_img: multispectral tiff, output_img: false color
	composite RGB image (GTiff).nRed,nGreen,nSWIR are index of red, green and
	SWIR in in put images.

	"""
	#call_subprocess(["gdal_translate","-co","PHOTOMETRIC=RGB","-scale","0","300","-ot","Byte","-b",str(nSWIR),"-b",str(nRed),"-b",str(nGreen),input_img,output_img])
	call_subprocess(["otbcli_Convert", "-in", input_img, "-out", output_img, "uint8", "-type", "linear"])

def burn_polygons_edges(input_img,input_vec):
	"""Burn polygon borders onto an image with the following symbology:
	 
	- cloud and cloud shadows: green
	- snow: magenta
	- convert mask polygons to lines
	
	"""
        
	#Save temporary file in working directory
        
	#Retrieve directory from input vector file
	input_dir=os.path.dirname(input_vec)
	#TODO move to snowdetector class?
	#Get unique identifier for the temporary file
	unique_filename=uuid.uuid4()
	tmp_line=op.join(input_dir,str(unique_filename))
	print "tmpline: " + str(tmp_line)

        #print "gdal version " + gdal.VersionInfo.str()
        
	call_subprocess(["ogr2ogr","-overwrite","-nlt","MULTILINESTRING",tmp_line+".shp",input_vec])

        if gdal.VersionInfo() >= 2000000:
                print "GDAL version >= 2.0 detected. Where statement syntax have changed in gdal."
                # 2) rasterize cloud and cloud shadows polygon borders in green
	        call_subprocess(["gdal_rasterize","-b","1","-b","2","-b","3","-burn","0","-burn","255","-burn","0","-where",'DN=2',"-l",str(unique_filename),tmp_line+".shp",input_img])
	        # 3) rasterize snow polygon borders in magenta
	        call_subprocess(["gdal_rasterize","-b","1","-b","2","-b","3","-burn","255","-burn","0","-burn","255","-where",'DN=1',"-l",str(unique_filename),tmp_line+".shp",input_img])
        else:
                print "GDAL version <2."
                # 2) rasterize cloud and cloud shadows polygon borders in green
	        call_subprocess(["gdal_rasterize","-b","1","-b","2","-b","3","-burn","0","-burn","255","-burn","0","-where","'DN=\"2\"'","-l",str(unique_filename),tmp_line+".shp",input_img])
	        # 3) rasterize snow polygon borders in magenta
	        call_subprocess(["gdal_rasterize","-b","1","-b","2","-b","3","-burn","255","-burn","0","-burn","255","-where","'DN=\"1\"'","-l",str(unique_filename),tmp_line+".shp",input_img])
                
        # 4) remove tmp_line files
	for shp in glob.glob(tmp_line+"*"):
		os.remove(shp)

class snow_detector :
	def __init__(self, data):

		self.version = VERSION
		#Parse general parameters

		general=data["general"]
		self.path_tmp=str(general.get("pout"))
		self.ram=general.get("ram", 512)
		try:
			nbDefaultThreads = multiprocessing.cpu_count()
		except NotImplementedError:
			print "Cannot get max number of CPU on the system. nbDefaultThreads set to 1."  
			nbDefaultThreads = 1
		self.nbThreads=general.get("nbThreads", nbDefaultThreads)
		self.mode=general.get("mode")
		self.generate_vector=general.get("generate_vector", False)
		self.do_preprocessing=general.get("preprocessing", False)
		self.do_postprocessing=True
		self.nodata=-10000 #TODO parse json if needed
		self.multi=general.get("multi", 1) # Multiplier to handle S2 scaling
		#Parse cloud data
		cloud=data["cloud"]
		self.rf=cloud.get("rf")
		self.rRed_darkcloud=cloud.get("red_darkcloud")
		self.rRed_darkcloud *= self.multi
		self.rRed_backtocloud=cloud.get("red_backtocloud")
		self.rRed_backtocloud *= self.multi
		self.shadow_mask=cloud.get("shadow_mask")
		self.all_cloud_mask=cloud.get("all_cloud_mask")
		self.high_cloud_mask=cloud.get("high_cloud_mask")
		#Parse input parameters
		inputs=data["inputs"]
		if(self.do_preprocessing):
			self.vrt=str(inputs.get("vrt")) 
		#self.img=str(inputs.get("image"))
		self.dem=str(inputs.get("dem"))
		self.cloud_init=str(inputs.get("cloud_mask"))
		
		#bands paths
		green_band=inputs["green_band"]
		gb_path=green_band["path"]
		gb_no=green_band["noBand"]

		gb_dataset = gdal.Open(gb_path, GA_ReadOnly)
		gb_path_extracted=op.join(self.path_tmp, "green_band_extracted.tif")
		if gb_dataset.RasterCount > 1:
			print "extracting green band"
			call_subprocess(["gdal_translate", "-of","GTiff","-ot","Int16","-a_nodata", str(self.nodata),"-b",str(gb_no),gb_path,gb_path_extracted])
		else:
			copyfile(gb_path, gb_path_extracted)

		red_band=inputs["red_band"]
		rb_path=red_band["path"]
		rb_no=red_band["noBand"]

		rb_dataset = gdal.Open(rb_path, GA_ReadOnly)
		rb_path_extracted=op.join(self.path_tmp, "red_band_extracted.tif")
		if rb_dataset.RasterCount > 1:
			print "extracting red band"
			call_subprocess(["gdal_translate", "-of","GTiff","-ot","Int16","-a_nodata", str(self.nodata),"-b",str(rb_no),rb_path,rb_path_extracted])
		else:
			copyfile(rb_path, rb_path_extracted)

		swir_band=inputs["swir_band"]
		sb_path=swir_band["path"]
		sb_no=swir_band["noBand"]
		
		sb_dataset = gdal.Open(sb_path, GA_ReadOnly)
		sb_path_extracted=op.join(self.path_tmp, "swir_band_extracted.tif")
		if sb_dataset.RasterCount > 1:
			print "extracting swir band"
			call_subprocess(["gdal_translate", "-of","GTiff","-ot","Int16","-a_nodata", str(self.nodata),"-b",str(sb_no),sb_path,sb_path_extracted])

		else:
			copyfile(sb_path, sb_path_extracted)

		#check for same res
		gb_dataset = gdal.Open(gb_path_extracted, GA_ReadOnly)
		rb_dataset = gdal.Open(rb_path_extracted, GA_ReadOnly)
		sb_dataset = gdal.Open(sb_path_extracted, GA_ReadOnly)
		
		gb_resolution = gb_dataset.GetGeoTransform()[1]
		rb_resolution = rb_dataset.GetGeoTransform()[1]
		sb_resolution = sb_dataset.GetGeoTransform()[1]
		print "green band resolution : " + str(gb_resolution)
		print "red band resolution : " + str(rb_resolution)
		print "swir band resolution : " + str(sb_resolution)
		#test if different reso
		gb_path_resampled=op.join(self.path_tmp, "green_band_resampled.tif")
		rb_path_resampled=op.join(self.path_tmp, "red_band_resampled.tif")
		sb_path_resampled=op.join(self.path_tmp, "swir_band_resampled.tif")
		if not gb_resolution == rb_resolution == sb_resolution:
			print "resolution is different among band files"
			#gdalwarp to max reso
			max_res = max(gb_resolution, rb_resolution, sb_resolution)
			print "cubic resampling to " + str(max_res) + "of resolution" 
			call_subprocess(["gdalwarp", "-overwrite","-r","cubic","-tr", str(max_res),str(max_res),gb_path_extracted,gb_path_resampled])
			call_subprocess(["gdalwarp", "-overwrite","-r","cubic","-tr", str(max_res),str(max_res),rb_path_extracted,rb_path_resampled])
			call_subprocess(["gdalwarp", "-overwrite","-r","cubic","-tr", str(max_res),str(max_res),sb_path_extracted,sb_path_resampled])
		else:
			gb_path_resampled=gb_path_extracted
			rb_path_resampled=rb_path_extracted
			sb_path_resampled=sb_path_extracted
			
		#build vrt
		print "building bands vrt"
		self.img=op.join(self.path_tmp, "lis.vrt")
		call_subprocess(["gdalbuildvrt","-separate", self.img, sb_path_resampled, rb_path_resampled, gb_path_resampled])
		
		#Set bands parameters
		self.nGreen=3
		self.nRed=2
		self.nSWIR=1
		
		#Parse snow parameters
		snow=data["snow"]
		self.dz=snow.get("dz")
		self.ndsi_pass1=snow.get("ndsi_pass1")
		self.rRed_pass1=snow.get("red_pass1")
		self.rRed_pass1*=self.multi
		self.ndsi_pass2=snow.get("ndsi_pass2")
		self.rRed_pass2=snow.get("red_pass2")
		self.rRed_pass2*=self.multi
		self.fsnow_lim=snow.get("fsnow_lim")
		self.fsnow_total_lim=snow.get("fsnow_total_lim")
		#Build useful paths
		self.redBand_path=op.join(self.path_tmp,"red.tif")
		self.ndsi_pass1_path=op.join(self.path_tmp,"pass1.tif")
		self.cloud_refine=op.join(self.path_tmp,"cloud_refine.tif")
		self.nodata_path=op.join(self.path_tmp, "nodata_mask.tif")
		
		# if self.mode == "spot":
		# 	self.nGreen=1 # Index of green band
		# 	self.nSWIR=4 # Index of SWIR band (1 to 3 µm) = band 11 (1.6 µm) in S2
		# 	self.nRed=2 # Index of red band
		# 	self.nodata=-10000 # no-data value
		# elif self.mode == "landsat":
		# 	self.nGreen=3
		# 	self.nSWIR=6
		# 	self.nRed=4 
		# 	self.nodata=-10000
		# elif self.mode == "s2":
		# 	sentinel_2_preprocessing()
		# 	#Set generic band index for Sentinel-2
		# 	self.nGreen=1
		# 	self.nRed=2
		# 	self.nSWIR=3
		# else:
		# 	sys.exit("Supported modes are spot4,landsat and s2.")

	def detect_snow(self, nbPass):
		#Set maximum ITK threads
		os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"]=str(self.nbThreads)
		#External preprocessing
		if self.do_preprocessing: 
			dem_builder.build_dem(self.vrt, self.img, self.dem)
			
		#Compute NoData mask
		call_subprocess(["otbcli_BandMath","-il",self.img ,"-out", self.nodata_path ,"uint8","-ram",str(self.ram),"-exp", "im1b1=="+str(self.nodata)+"?1:0"])
			
		if nbPass >= 0 :
			self.pass0()
		if nbPass >= 1 :
			self.pass1()
		if nbPass == 2 :
			self.pass2()
				
		#Gdal polygonize (needed to produce composition)
		#TODO: Study possible loss and issue with vectorization product
		polygonize(op.join(self.path_tmp,"final_mask.tif"),op.join(self.path_tmp,"final_mask.tif"),op.join(self.path_tmp,"final_mask_vec.shp"))

		#RGB composition
		composition_RGB(self.img,op.join(self.path_tmp,"composition.tif"))

		#Burn polygons edges on the composition
		#TODO add pass1 snow polygon in yellow
		burn_polygons_edges(op.join(self.path_tmp,"composition.tif"),op.join(self.path_tmp,"final_mask_vec.shp"))

		#External postprocessing
		if self.do_postprocessing:
			format_output.format_LIS(self) 
			
	def pass0(self):
		#Pass -1 : generate custom cloud mask
        #Extract red band
		call_subprocess(["gdal_translate", "-a_nodata", str(self.nodata),"-ot","Int16","-b",str(self.nRed),self.img,self.redBand_path])
		dataset = gdal.Open( self.redBand_path, GA_ReadOnly )
		
		xSize=dataset.RasterXSize
		ySize=dataset.RasterYSize
		
		#Get geotransform to retrieve resolution
		geotransform = dataset.GetGeoTransform() 
		
		#resample red band using multiresolution pyramid
		call_subprocess(["gdalwarp","-r","bilinear","-ts",str(xSize/self.rf),str(ySize/self.rf),self.redBand_path,op.join(self.path_tmp,"red_coarse.tif")])
		
		#Resample red band nn
		#FIXME: use MACCS resampling filter contribute by J. Michel here
		call_subprocess(["gdalwarp","-r","near","-ts",str(xSize),str(ySize),op.join(self.path_tmp,"red_coarse.tif"),op.join(self.path_tmp,"red_nn.tif")])
		
		#edit result to set the resolution to the input image resolution
		#TODO need to find a better solution and also guess the input spacing (using maccs resampling filter)
		call_subprocess(["gdal_edit.py","-tr",str(geotransform[1]),str(geotransform[5]),op.join(self.path_tmp,"red_nn.tif")])
		
		#Extract shadow mask
		call_subprocess(["compute_cloud_mask", self.cloud_init, str(self.all_cloud_mask), op.join(self.path_tmp,"all_cloud_mask.tif")]) 
		call_subprocess(["compute_cloud_mask", self.cloud_init, str(self.shadow_mask), op.join(self.path_tmp,"shadow_mask.tif")])
		call_subprocess(["compute_cloud_mask", self.cloud_init, str(self.high_cloud_mask), op.join(self.path_tmp,"high_cloud_mask.tif")])
		cond_cloud2="im3b1>" + str(self.rRed_darkcloud)
		condition_shadow= "((im1b1==1 and " + cond_cloud2 + ") or im2b1==1 or im4b1==1)"
		print condition_shadow
		call_subprocess(["otbcli_BandMath","-il",op.join(self.path_tmp,"all_cloud_mask.tif"), op.join(self.path_tmp,"shadow_mask.tif"),op.join(self.path_tmp,"red_nn.tif"), op.join(self.path_tmp,"high_cloud_mask.tif"),"-out",self.cloud_refine+GDAL_OPT,"uint8","-ram",str(self.ram),"-exp",condition_shadow])

	def pass1(self):
		#Pass1 : NDSI threshold
		ndsi_formula= "(im1b"+str(self.nGreen)+"-im1b"+str(self.nSWIR)+")/(im1b"+str(self.nGreen)+"+im1b"+str(self.nSWIR)+")"
		print "ndsi formula: ",ndsi_formula
		
		#Use 255 not 1 here because of bad handling of 1 byte tiff by otb)
		#FIXME
		condition_pass1= "(im2b1!=255 and ("+ndsi_formula+")>"+ str(self.ndsi_pass1) + " and im1b"+str(self.nRed)+"> " + str(self.rRed_pass1) + ")"
		call_subprocess(["otbcli_BandMath","-il",self.img,self.cloud_refine,"-out",self.ndsi_pass1_path+GDAL_OPT,"uint8","-ram",str(self.ram),"-exp",condition_pass1 + "?1:0"])
		
		#Update the cloud mask (again)
		#Use 255 not 1 here because of bad handling of 1 byte tiff by otb)
		#FIXME
		condition_cloud_pass1= "(im1b1==255 or (im2b1!=255 and im3b1==1 and im4b1> " + str(self.rRed_backtocloud) + "))"
		call_subprocess(["otbcli_BandMath","-il",self.cloud_refine,self.ndsi_pass1_path,self.cloud_init,self.redBand_path,"-out",op.join(self.path_tmp,"cloud_pass1.tif")+GDAL_OPT,"uint8","-ram",str(self.ram),"-exp",condition_cloud_pass1 + "?1:0"])
		
	def pass2(self):
		ndsi_formula= "(im1b"+str(self.nGreen)+"-im1b"+str(self.nSWIR)+")/(im1b"+str(self.nGreen)+"+im1b"+str(self.nSWIR)+")"
		#Pass 2: compute snow fraction (c++)
		nb_snow_pixels = histo_utils_ext.compute_nb_pixels_between_bounds(self.ndsi_pass1_path, 0 , 255)
		print "Number of snow pixels ", nb_snow_pixels
		
		if (nb_snow_pixels > self.fsnow_total_lim):
			#Pass 2: determine the Zs elevation fraction (c++)
			#Save histogram values for logging
			histo_log=op.join(self.path_tmp,"histogram.txt")
			#c++ function
			self.zs=histo_utils_ext.compute_snowline(self.dem,self.ndsi_pass1_path,op.join(self.path_tmp,"cloud_pass1.tif"), self.dz, self.fsnow_lim, False, -2, -self.dz/2, histo_log) 
			
			print "computed ZS:", self.zs
			
			#Test zs value (-1 means that no zs elevation was found)
			if (self.zs !=-1):
				#NDSI threshold again
				#Use 255 not 1 here because of bad handling of 1 byte tiff by otb)
				#FIXME
				condition_pass2= "(im3b1 != 255) and (im2b1>" + str(self.zs) + ") and (" + ndsi_formula + "> " + str(self.ndsi_pass2) + ") and (im1b"+str(self.nRed)+">" + str(self.rRed_pass2) + ")"

				call_subprocess(["otbcli_BandMath","-il",self.img,self.dem,self.cloud_refine,"-out",op.join(self.path_tmp,"pass2.tif")+GDAL_OPT,"uint8","-ram",str(1024),"-exp", condition_pass2 + "?1:0"])
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
				#empty image pass2 is needed for computing snow_all
				call_subprocess(["otbcli_BandMath", "-il", op.join(self.path_tmp,"pass1.tif"), "-out", op.join(self.path_tmp,"pass2.tif")+GDAL_OPT, "uint8", "-ram", str(1024), "-exp", "0"])

		else:
			generic_snow_path=self.ndsi_pass1_path
			#empty image pass2 is needed for computing snow_all
			call_subprocess(["otbcli_BandMath", "-il", op.join(self.path_tmp,"pass1.tif"), "-out", op.join(self.path_tmp,"pass2.tif")+GDAL_OPT, "uint8", "-ram", str(1024), "-exp", "0"])
			
		if self.generate_vector:
			#Generate polygons for pass3 (useful for quality check)
			polygonize(generic_snow_path,generic_snow_path,op.join(self.path_tmp,"pass3_vec.shp"))
			
		# Final update of the cloud mask (use 255 not 1 here because of bad handling of 1 byte tiff by otb)
		condition_final= "(im2b1==255)?1:((im1b1==255) or ((im3b1>0) and (im4b1> " + str(self.rRed_backtocloud) + ")))?2:0"
						
		call_subprocess(["otbcli_BandMath","-il",self.cloud_refine,generic_snow_path,self.cloud_init,self.redBand_path,"-out",op.join(self.path_tmp,"final_mask.tif")+GDAL_OPT_2B,"uint8","-ram",str(self.ram),"-exp",condition_final])
		call_subprocess(["compute_snow_mask", op.join(self.path_tmp,"pass1.tif"), op.join(self.path_tmp,"pass2.tif"), op.join(self.path_tmp,"cloud_pass1.tif"), op.join(self.path_tmp,"cloud_refine.tif"), op.join(self.path_tmp, "snow_all.tif")])

	def pass3(self):
		#Fuse pass1 and pass2 (use 255 not 1 here because of bad handling of 1 byte tiff by otb)
		#FIXME
		condition_pass3= "(im1b1 == 255 or im2b1 == 255)"
		call_subprocess(["otbcli_BandMath","-il",self.ndsi_pass1_path,op.join(self.path_tmp,"pass2.tif"),"-out",op.join(self.path_tmp,"pass3.tif")+GDAL_OPT,"uint8","-ram",str(self.ram),"-exp",condition_pass3 + "?1:0"])

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
		call_subprocess(["gdal_translate", "-a_nodata", str(self.nodata),"-ot","Int16","-b",str(nGreen),s2_r1_img_path[0],greenBand_path])
		call_subprocess(["gdalwarp","-r","cubic","-tr","20","-20",greenBand_path,greenBand_resample_path])

		#Extract red bands and sample to 20 meters
		#FIXME Use multi resolution pyramid application or new resampling filter fontribute by J. Michel hear
		call_subprocess(["gdal_translate", "-a_nodata", str(self.nodata),"-ot","Int16","-b",str(nRed),s2_r1_img_path[0],redBand_path])
		call_subprocess(["gdalwarp","-r","cubic","-tr","20","-20",redBand_path,redBand_resample_path])

		#Extract SWIR
		call_subprocess(["gdal_translate", "-a_nodata", str(self.nodata),"-ot","Int16","-b",str(nSWIR),s2_r2_img_path[0],swirBand_path])
						
		#Concatenate all bands in a single image
		concat_s2=op.join(path_tmp,"concat_s2.tif")
		call_subprocess(["otbcli_ConcatenateImages","-il",greenBand_resample_path,redBand_resample_path,swirBand_path,"-out",concat_s2,"int16","-ram",str(ram)])
						
		#img variable is used later to compute snow mask
		self.img=concat_s2
		self.redBand_path=op.join(path_tmp,"red.tif")



