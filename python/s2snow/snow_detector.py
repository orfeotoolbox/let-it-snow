#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import os
import os.path as op
import shutil
import logging
from lxml import etree

import gdal
from gdalconst import GA_ReadOnly, GA_Update

# OTB Applications
import otbApplication as otb

# Preprocessing script
from s2snow.dem_builder import build_dem

# Import python decorators for the different needed OTB applications
from s2snow.app_wrappers import compute_snow_mask, compute_cloud_mask
from s2snow.app_wrappers import band_math, compute_snow_line

# Import utilities for snow detection
from s2snow.utils import polygonize, extract_band, burn_polygons_edges, composition_RGB
from s2snow.utils import compute_percent, format_SEB_VEC_values, get_raster_as_array

# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

# Build gdal option to generate maks of 1 byte using otb extended filename
# syntaxx
GDAL_OPT = "?&gdal:co:NBITS=1&gdal:co:COMPRESS=DEFLATE"


"""This module does implement the snow detection (all passes)"""
class snow_detector:
    def __init__(self, data):

        # Parse general parameters
        general = data["general"]
        self.path_tmp = str(general.get("pout"))
        self.ram = general.get("ram", 512)
        self.nbThreads = general.get("nb_threads", None)
        logging.info("Actual number of threads: " + str(self.nbThreads))
        self.mode = general.get("mode")
        self.do_preprocessing = general.get("preprocessing", False)
        self.nodata = general.get("nodata", -10000)
        self.multi = general.get("multi", 1)  # Multiplier to handle S2 scaling

        # Resolutions in meter for the snow product
        # (if -1 the target resolution is equal to the max resolution of the input band)
        self.target_resolution = general.get("target_resolution", -1)

        # Parse vector option
        vector_options = data["vector"]
        self.generate_vector = vector_options.get("generate_vector", True)
        self.generate_intermediate_vectors = vector_options.get("generate_intermediate_vectors", False)
        self.use_gdal_trace_outline = vector_options.get("use_gdal_trace_outline", True)
        self.gdal_trace_outline_dp_toler = vector_options.get("gdal_trace_outline_dp_toler", 0)
        self.gdal_trace_outline_min_area = vector_options.get("gdal_trace_outline_min_area", 0)

        # Parse cloud data
        cloud = data["cloud"]
        self.rf = cloud.get("rf")
        self.rRed_darkcloud = cloud.get("red_darkcloud")
        self.rRed_darkcloud *= self.multi
        self.rRed_backtocloud = cloud.get("red_backtocloud")
        self.rRed_backtocloud *= self.multi
        self.shadow_in_mask = cloud.get("shadow_in_mask")
        self.shadow_out_mask = cloud.get("shadow_out_mask")
        self.all_cloud_mask = cloud.get("all_cloud_mask")
        self.high_cloud_mask = cloud.get("high_cloud_mask")

        ## Strict cloud mask usage (off by default)
        ## If set to True no pixel from the cloud mask will be marked as snow
        self.strict_cloud_mask = cloud.get("strict_cloud_mask", False)

        ## Suppress snow area surrounded by cloud (off by default)
        self.rm_snow_inside_cloud = cloud.get("rm_snow_inside_cloud", False)
        self.dilation_radius = cloud.get("rm_snow_inside_cloud_dilation_radius", 5)
        self.cloud_threshold = cloud.get("rm_snow_inside_cloud_threshold", 0.85)
        self.cloud_min_area_size = cloud.get("rm_snow_inside_cloud_min_area", 25000)

        # Parse input parameters
        inputs = data["inputs"]
        if self.do_preprocessing:
            self.vrt = str(inputs.get("vrt"))
        # self.img=str(inputs.get("image"))
        self.dem = str(inputs.get("dem"))
        self.cloud_init = str(inputs.get("cloud_mask"))

        ## Get div mask if available
        self.slope_mask_path = None
        if inputs.get("div_mask") and inputs.get("div_slope_thres"):
            self.div_mask = str(inputs.get("div_mask"))
            self.div_slope_thres = inputs.get("div_slope_thres")
            self.slope_mask_path = op.join(self.path_tmp, "bad_slope_correction_mask.tif")

            # Extract the bad slope correction flag
            bandMathSlopeFlag = band_math([self.div_mask],
                                    self.slope_mask_path,
                                    "im1b1>="+str(self.div_slope_thres)+"?1:0",
                                    self.ram,
                                    otb.ImagePixelType_uint8)
            bandMathSlopeFlag.ExecuteAndWriteOutput()
            bandMathSlopeFlag = None

        # bands paths
        gb_path_extracted = extract_band(inputs, "green_band", self.path_tmp, self.nodata)
        rb_path_extracted = extract_band(inputs, "red_band", self.path_tmp, self.nodata)
        sb_path_extracted = extract_band(inputs, "swir_band", self.path_tmp, self.nodata)

        # Keep the input product directory basename as product_id
        self.product_id = op.basename(op.dirname(inputs["green_band"]["path"]))

        # check for same res
        gb_dataset = gdal.Open(gb_path_extracted, GA_ReadOnly)
        rb_dataset = gdal.Open(rb_path_extracted, GA_ReadOnly)
        sb_dataset = gdal.Open(sb_path_extracted, GA_ReadOnly)
        gb_resolution = gb_dataset.GetGeoTransform()[1]
        rb_resolution = rb_dataset.GetGeoTransform()[1]
        sb_resolution = sb_dataset.GetGeoTransform()[1]
        logging.info("green band resolution : " + str(gb_resolution))
        logging.info("red band resolution : " + str(rb_resolution))
        logging.info("swir band resolution : " + str(sb_resolution))
        gb_dataset = None
        rb_dataset = None
        sb_dataset = None

        # test if different reso
        gb_path_resampled = op.join(self.path_tmp, "green_band_resampled.tif")
        rb_path_resampled = op.join(self.path_tmp, "red_band_resampled.tif")
        sb_path_resampled = op.join(self.path_tmp, "swir_band_resampled.tif")

        # target resolution of the snow product
        max_res = max(gb_resolution, rb_resolution, sb_resolution)
        if self.target_resolution == -1:
            self.target_resolution = max(gb_resolution, rb_resolution, sb_resolution)
        else:
            logging.info("Snow product will be at the resolution of " + str(self.target_resolution) + " meters.")

        # Change target resolution
        if rb_resolution != self.target_resolution:
            logging.info("cubic resampling of red band to " + str(self.target_resolution) + " meters.")
            gdal.Warp(
                rb_path_resampled,
                rb_path_extracted,
                resampleAlg=gdal.GRIORA_Cubic,
                xRes=self.target_resolution,
                yRes=self.target_resolution)
        else:
            rb_path_resampled = rb_path_extracted

        if gb_resolution != self.target_resolution:
            logging.info("cubic resampling of green band to " + str(self.target_resolution) + " meters.")
            gdal.Warp(
                gb_path_resampled,
                gb_path_extracted,
                resampleAlg=gdal.GRIORA_Cubic,
                xRes=self.target_resolution,
                yRes=self.target_resolution)
        else:
            gb_path_resampled = gb_path_extracted

        if sb_resolution != self.target_resolution:
            logging.info("cubic resampling of swir band to " + str(self.target_resolution) + " meters.")
            gdal.Warp(
                sb_path_resampled,
                sb_path_extracted,
                resampleAlg=gdal.GRIORA_Cubic,
                xRes=self.target_resolution,
                yRes=self.target_resolution)
        else:
            sb_path_resampled = sb_path_extracted

        # build vrt
        logging.info("building bands vrt")
        self.img = op.join(self.path_tmp, "lis.vrt")

        gdal.BuildVRT(self.img,
                      [sb_path_resampled,
                       rb_path_resampled,
                       gb_path_resampled],
                      separate=True)

        # Set bands parameters
        self.nGreen = 3
        self.nRed = 2
        self.nSWIR = 1

        # Parse snow parameters
        snow = data["snow"]
        self.dz = snow.get("dz")
        self.ndsi_pass1 = snow.get("ndsi_pass1")
        self.rRed_pass1 = snow.get("red_pass1")
        self.rRed_pass1 *= self.multi
        self.ndsi_pass2 = snow.get("ndsi_pass2")
        self.rRed_pass2 = snow.get("red_pass2")
        self.rRed_pass2 *= self.multi
        self.fsnow_lim = snow.get("fsnow_lim")
        self.fsnow_total_lim = snow.get("fsnow_total_lim")
        self.zs = -1  # default value when zs is not set

        # Define the minimum amount of clear pixels altitude bin
        self.fclear_lim = snow.get("fclear_lim", 0.1)

        # Define label for output snow product
        self.label_no_snow = "0"
        self.label_snow = "100"
        self.label_cloud = "205"
        self.label_no_data = "254"

        # Build useful paths
        self.pass1_path = op.join(self.path_tmp, "pass1.tif")
        self.pass2_path = op.join(self.path_tmp, "pass2.tif")
        self.pass3_path = op.join(self.path_tmp, "pass3.tif")
        self.redBand_path = op.join(self.path_tmp, "red.tif")
        self.all_cloud_path = op.join(self.path_tmp, "all_cloud_mask.tif")
        self.cloud_pass1_path = op.join(self.path_tmp, "cloud_pass1.tif")
        self.cloud_refine_path = op.join(self.path_tmp, "cloud_refine.tif")
        self.nodata_path = op.join(self.path_tmp, "nodata_mask.tif")
        self.mask_backtocloud = op.join(self.path_tmp, "mask_backtocloud.tif")

        # Prepare product directory
        self.product_path = op.join(self.path_tmp, "LIS_PRODUCTS")
        if not op.exists(self.product_path):
            os.makedirs(self.product_path)

        # Build product file paths
        self.snow_all_path = op.join(self.product_path, "LIS_SNOW_ALL.TIF")
        self.final_mask_path = op.join(self.product_path, "LIS_SEB.TIF")
        self.final_mask_vec_path = op.join(self.product_path, "LIS_SEB_VEC.shp")
        self.composition_path = op.join(self.product_path, "LIS_COMPO.TIF")
        self.histogram_path = op.join(self.product_path, "LIS_HISTO.TXT")
        self.metadata_path = op.join(self.product_path, "LIS_METADATA.XML")

    def detect_snow(self, nbPass):
        # Set maximum ITK threads
        if self.nbThreads:
            os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(self.nbThreads)

        # External preprocessing
        if self.do_preprocessing:
            # Declare a pout dem in the output directory
            pout_resampled_dem = op.join(self.path_tmp, "dem_resampled.tif")
            build_dem(self.dem, self.img, pout_resampled_dem, self.ram, self.nbThreads)

            # Change self.dem to use the resampled DEM (output of build_dem) in this case
            self.dem = pout_resampled_dem

        # Initialize the mask
        noDataMaskExpr = "im1b1==" + str(self.nodata) + "?1:0"
        bandMath = band_math(
            [self.img],
            self.nodata_path,
            noDataMaskExpr,
            self.ram)
        bandMath.ExecuteAndWriteOutput()
        bandMath = None

        if nbPass >= 0:
            self.pass0()
        if nbPass >= 1:
            self.pass1()
        if nbPass == 2:
            self.pass2()

        # RGB composition
        composition_RGB(
            self.img,
            self.composition_path,
            self.nSWIR,
            self.nRed,
            self.nGreen,
            self.multi)

        # Gdal polygonize (needed to produce composition)
        # TODO: Study possible loss and issue with vectorization product
        if self.generate_vector:
            polygonize(
                self.final_mask_path,
                self.final_mask_path,
                self.final_mask_vec_path,
                self.use_gdal_trace_outline,
                self.gdal_trace_outline_min_area,
                self.gdal_trace_outline_dp_toler)

        # Burn polygons edges on the composition
        # TODO add pass1 snow polygon in yellow
        burn_polygons_edges(
            self.composition_path,
            self.final_mask_path,
            self.label_snow,
            self.label_cloud,
            self.ram)

        # Product formating
        #~ format_SEB_VEC_values(self.final_mask_vec_path,
                              #~ self.label_snow,
                              #~ self.label_cloud,
                              #~ self.label_no_data)
        self.create_metadata()

    def create_metadata(self):
        # Compute and create the content for the product metadata file.
        snow_percent = compute_percent(self.final_mask_path,
                                       self.label_snow,
                                       self.label_no_data)
        logging.info("Snow percent = " + str(snow_percent))

        cloud_percent = compute_percent(self.final_mask_path,
                                        self.label_cloud,
                                        self.label_no_data)
        logging.info("Cloud percent = " + str(cloud_percent))

        root = etree.Element("Source_Product")
        etree.SubElement(root, "PRODUCT_ID").text = self.product_id
        egil = etree.SubElement(root, "Global_Index_List")
        etree.SubElement(egil, "QUALITY_INDEX", name='ZS').text = str(self.zs)
        etree.SubElement(
            egil,
            "QUALITY_INDEX",
            name='SnowPercent').text = str(snow_percent)
        etree.SubElement(
            egil,
            "QUALITY_INDEX",
            name='CloudPercent').text = str(cloud_percent)
        et = etree.ElementTree(root)
        et.write(self.metadata_path, pretty_print=True)

    def extract_all_clouds(self):
        if self.mode == 'lasrc':
            # Extract shadow wich corresponds to  all cloud shadows in larsc product
            logging.info("lasrc mode -> extract all clouds from LASRC product using ComputeCloudMask application...")
            computeCMApp = compute_cloud_mask(
                self.cloud_init,
                self.all_cloud_path + GDAL_OPT,
                str(self.all_cloud_mask),
                self.ram,
                otb.ImagePixelType_uint8)
            computeCMApp.ExecuteAndWriteOutput()
            computeCMApp = None 
        else:
            if self.mode == 'sen2cor':
                logging.info("sen2cor mode -> extract all clouds from SCL layer...")
                logging.info("All clouds in sen2cor SCL layer corresponds to:")
                logging.info("- label == 3 -> Cloud shadows")
                logging.info("- label == 8 -> Cloud medium probability")
                logging.info("- label == 9 -> Cloud high probability")
                logging.info("- label == 10 -> Thin cirrus")
                condition_all_clouds = "im1b1==3 || im1b1==8 || im1b1==9 || im1b1==10"
            else:
                condition_all_clouds = "im1b1 > 0"

                bandMathAllCloud = band_math(
                    [self.cloud_init],
                    self.all_cloud_path + GDAL_OPT,
                    "("+condition_all_clouds+" > 0)?1:0",
                    self.ram,
                    otb.ImagePixelType_uint8)
                bandMathAllCloud.ExecuteAndWriteOutput()
                bandMathAllCloud = None

    def extract_cloud_shadows(self):
        shadow_mask_path = op.join(self.path_tmp, "shadow_mask.tif") + GDAL_OPT

        # Extract shadow masks differently if sen2cor or MAJA
        if self.mode == 'sen2cor':
            logging.info("sen2cor mode -> extract all clouds from SCL layer...")
            logging.info("- label == 3 -> Cloud shadows")
            bandMathShadow = band_math(
                [self.cloud_init],
                shadow_mask_path,
                "(im1b1 == 3)",
                self.ram,
                otb.ImagePixelType_uint8)
            bandMathShadow.ExecuteAndWriteOutput()
            bandMathShadow = None
        else:
            # First extract shadow wich corresponds to shadow of clouds inside the
            # image
            computeCMApp = compute_cloud_mask(
                self.cloud_init,
                op.join(self.path_tmp, "shadow_in_mask.tif") + GDAL_OPT,
                str(self.shadow_in_mask),
                self.ram,
                otb.ImagePixelType_uint8)
            computeCMApp.ExecuteAndWriteOutput()
            computeCMApp = None

            # Then extract shadow mask of shadows from clouds outside the image
            computeCMApp = compute_cloud_mask(
                self.cloud_init,
                op.join(self.path_tmp, "shadow_out_mask.tif") + GDAL_OPT,
                str(self.shadow_out_mask),
                self.ram,
                otb.ImagePixelType_uint8)
            computeCMApp.ExecuteAndWriteOutput()
            computeCMApp = None

            # The output shadow mask corresponds to a OR logic between the 2 shadow
            # masks
            bandMathShadow = band_math(
                [op.join(self.path_tmp, "shadow_in_mask.tif"),
                 op.join(self.path_tmp, "shadow_out_mask.tif")],
                shadow_mask_path,
                "(im1b1 == 1) || (im2b1 == 1)",
                self.ram,
                otb.ImagePixelType_uint8)
            bandMathShadow.ExecuteAndWriteOutput()
            bandMathShadow = None

    def extract_high_clouds(self):
        high_clouds_mask_path = op.join(self.path_tmp, "high_cloud_mask.tif") + GDAL_OPT
        if self.mode == 'sen2cor':
            logging.info("sen2cor mode -> extract all clouds from SCL layer...")
            logging.info("- label == 10 -> Thin cirrus")
            bandMathHighClouds = band_math(
                [self.cloud_init],
                high_clouds_mask_path,
                "(im1b1 == 10)",
                self.ram,
                otb.ImagePixelType_uint8)
            bandMathHighClouds.ExecuteAndWriteOutput()
            bandMathHighClouds = None
        else:
            computeCMApp = compute_cloud_mask(
                self.cloud_init,
                high_clouds_mask_path,
                str(self.high_cloud_mask),
                self.ram,
                otb.ImagePixelType_uint8)
            computeCMApp.ExecuteAndWriteOutput()
            computeCMApp = None

    def extract_backtocloud_mask(self):
        cloud_mask_for_backtocloud = self.cloud_init

        if self.mode == 'sen2cor':
            logging.info("sen2cor mode -> extract all clouds from SCL layer...")
            logging.info("All clouds in sen2cor SCL layer corresponds to:")
            logging.info("- label == 3 -> Cloud shadows")
            logging.info("- label == 8 -> Cloud medium probability")
            logging.info("- label == 9 -> Cloud high probability")
            logging.info("- label == 10 -> Thin cirrus")
            condition_all_clouds = "im1b1==3 || im1b1==8 || im1b1==9 || im1b1==10"
        else:
            condition_all_clouds = "im1b1 > 0"
            
        condition_back_to_cloud = "("+condition_all_clouds+") and (im2b1 > " + str(self.rRed_backtocloud) + ")"
        bandMathBackToCloud = band_math(
            [cloud_mask_for_backtocloud, self.redBand_path],
            self.mask_backtocloud + GDAL_OPT,
            condition_back_to_cloud + "?1:0",
            self.ram,
            otb.ImagePixelType_uint8)
        bandMathBackToCloud.ExecuteAndWriteOutput()
        
    def pass0(self):
        # Pass -0 : generate custom cloud mask
        # Extract red band
        gdal.Translate(
            self.redBand_path,
            self.img,
            format='GTiff',
            outputType=gdal.GDT_Int16,
            noData=self.nodata,
            bandList=[self.nRed])

        dataset = gdal.Open(self.redBand_path, GA_ReadOnly)

        xSize = dataset.RasterXSize
        ySize = dataset.RasterYSize

        # Get geotransform to retrieve resolution
        geotransform = dataset.GetGeoTransform()
        dataset = None

        # resample red band using multiresolution pyramid
        gdal.Warp(
            op.join(self.path_tmp, "red_coarse.tif"),
            self.redBand_path,
            resampleAlg=gdal.GRIORA_Bilinear,
            width=xSize / self.rf,
            height=ySize / self.rf)

        # Resample red band nn
        # FIXME: use MAJA resampling filter contribute in OTB 5.6 here
        gdal.Warp(
            op.join(self.path_tmp, "red_nn.tif"),
            op.join(self.path_tmp, "red_coarse.tif"),
            resampleAlg=gdal.GRIORA_NearestNeighbour,
            width=xSize,
            height=ySize)

        # edit result to set the resolution to the input image resolution
        # TODO need to find a better solution and also guess the input spacing
        # (using maccs resampling filter)
        dataset = gdal.Open(op.join(self.path_tmp, "red_nn.tif"),
                            gdal.GA_Update)
        dataset.SetGeoTransform(geotransform)
        dataset = None

        ## Extract layers related to the cloud mask

        # Extract all cloud masks
        self.extract_all_clouds()

        # Extract cloud shadows mask
        self.extract_cloud_shadows()
        
        # Extract high clouds
        self.extract_high_clouds()

        # Extract also a mask for condition back to cloud
        self.extract_backtocloud_mask()

    def pass1(self):
        logging.info("Start pass 1")

        # Pass1 : NDSI threshold
        ndsi_formula = "(im1b" + str(self.nGreen) + "-im1b" + str(self.nSWIR) + \
            ")/(im1b" + str(self.nGreen) + "+im1b" + str(self.nSWIR) + ")"
        logging.info("ndsi formula: "+ ndsi_formula)

        # NDSI condition (ndsi > x and not cloud)
        condition_ndsi = "(im2b1!=1 and (" + ndsi_formula + ")>" + str(self.ndsi_pass1) + " "

        condition_pass1 = condition_ndsi + \
            " and im1b" + str(self.nRed) + "> " + str(self.rRed_pass1) + ")"

        bandMathPass1 = band_math(
            [self.img, self.all_cloud_path],
            self.pass1_path + GDAL_OPT,
            condition_pass1 + "?1:0",
            self.ram,
            otb.ImagePixelType_uint8)
        bandMathPass1.ExecuteAndWriteOutput()
        bandMathPass1 = None

        # create a working copy of all cloud mask
        shutil.copy(self.all_cloud_path, self.cloud_pass1_path)

        # apply pass 1.5 to discard uncertain snow area
        # warn this function update in-place both snow and cloud mask
        if self.rm_snow_inside_cloud:
            self.pass1_5(self.pass1_path,
                         self.cloud_pass1_path,
                         self.dilation_radius,
                         self.cloud_threshold,
                         self.cloud_min_area_size)

        # The computation of cloud refine is done below,
        # because the inital cloud may be updated within pass1_5

        # Refine cloud mask for snow detection
        cond_cloud2 = "im3b1>" + str(self.rRed_darkcloud)

        # this condition check if pass1_5 caused a cloud mask update
        condition_donuts = "(im1b1!=im5b1)"

        condition_shadow = "((im1b1==1 and " + cond_cloud2 + \
            ") or im2b1==1 or im4b1==1 or " + condition_donuts + ")"

        logging.info(condition_shadow)

        bandMathFinalShadow = band_math(
            [self.all_cloud_path,
             op.join(self.path_tmp, "shadow_mask.tif"),
             op.join(self.path_tmp, "red_nn.tif"),
             op.join(self.path_tmp, "high_cloud_mask.tif"),
             self.cloud_pass1_path],
            self.cloud_refine_path + GDAL_OPT,
            condition_shadow,
            self.ram,
            otb.ImagePixelType_uint8)
        bandMathFinalShadow.ExecuteAndWriteOutput()

        logging.info("End of pass 1")

    def pass1_5(self, snow_mask_path, cloud_mask_path, radius=1, cloud_threshold=0.85, min_area_size=25000):
        logging.info("Start pass 1.5")
        import numpy as np
        import scipy.ndimage as nd

        snow_mask = get_raster_as_array(snow_mask_path)
        cloud_mask = get_raster_as_array(cloud_mask_path)

        snow_mask_init = np.copy(snow_mask)

        discarded_snow_area = 0

        (snowlabels, nb_label) = nd.measurements.label(snow_mask)
        logging.info("There is " + str(nb_label) + " snow areas")

        # build the structuring element for dilation
        struct = np.zeros((2*radius+1, 2*radius+1))
        y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
        mask = x**2 + y**2 <= radius**2
        struct[mask] = 1

        logging.debug("Start loop on snow areas")

        # For each snow area
        for lab in range(1, nb_label+1):
            # Compute external contours
            logging.debug("Processing area " + str(lab))
            current_mask = np.where(snowlabels == lab, 1, 0)
            current_mask_area = np.count_nonzero(current_mask)
            logging.debug("Current area size = " + str(current_mask_area))
            if current_mask_area > min_area_size:
                logging.debug("Processing snow area of size = " + str(current_mask_area))
                patch_neige_dilat = nd.binary_dilation(current_mask, struct)
                logging.debug("Contour processing start")
                contour = np.where((snow_mask == 0) & (patch_neige_dilat == 1))

                # Compute percent of surronding cloudy pixels
                cloud_contour = cloud_mask[contour]
                # print cloud_contour
                logging.debug("Contour processing done.")

                result = np.bincount(cloud_contour)
                logging.debug(result)
                cloud_percent = 0
                if len(result) > 1:
                    cloud_percent = float(result[1]) / (result[0] + result[1])
                    logging.info(result)
                    logging.info(", " + str(cloud_percent*100) + "% of surrounding cloud")

                # Discard snow area where cloud_percent > threshold
                if cloud_percent > cloud_threshold:
                    logging.info("Updating snow mask...")
                    discarded_snow_area += 1
                    snow_mask = np.where(snowlabels == lab, 0, snow_mask)
                    logging.info("Updating snow mask...Done")
                    logging.info("End of processing area " + str(lab))

        logging.info(str(discarded_snow_area) + ' labels entoures de nuages (sur ' \
                     + str(nb_label) + ' labels)')

        (snowlabels, nb_label) = nd.measurements.label(snow_mask)

        logging.info(str(nb_label) + ' labels neige apres correction')

        # Update cloud mask with discared snow area
        updated_cloud_mask = np.where((snow_mask == 0) & (snow_mask_init == 1), 1, cloud_mask)
        dataset = gdal.Open(cloud_mask_path, GA_Update)
        band = dataset.GetRasterBand(1)
        band.WriteArray(updated_cloud_mask)
        dataset = None

        # Update snow mask
        dataset = gdal.Open(snow_mask_path, GA_Update)
        band = dataset.GetRasterBand(1)
        band.WriteArray(snow_mask)
        dataset = None

        logging.info("End of pass 1.5")

    def pass2(self):
        # Compute snow fraction in the pass1 image (including nodata pixels)
        snow_fraction = compute_percent(self.pass1_path, 1)/100
        logging.info("snow fraction in pass1 image:" + str(snow_fraction))

        # Compute Zs elevation fraction and histogram values
        # We compute it in all case as we need to check histogram values to
        # detect cold clouds in optionnal pass4

        snow_line_app = compute_snow_line(
            self.dem,
            self.pass1_path,
            self.cloud_pass1_path,
            self.dz,
            self.fsnow_lim,
            self.fclear_lim,
            False,
            -2,
            -self.dz / 2,
            self.histogram_path,
            self.ram)

        snow_line_app.Execute()

        self.zs = snow_line_app.GetParameterInt("zs")

        logging.info("computed ZS:" + str(self.zs))

        if snow_fraction > self.fsnow_total_lim:
            # Test zs value (-1 means that no zs elevation was found)
            if self.zs != -1:
                # NDSI threshold again
                ndsi_formula = "(im1b" + str(self.nGreen) + "-im1b" + str(self.nSWIR) + \
                               ")/(im1b" + str(self.nGreen) + "+im1b" + str(self.nSWIR) + ")"
                
                condition_pass2 = "(im3b1 != 1) and (im2b1>" + str(self.zs) + ")" \
                                  + " and (" + ndsi_formula + "> " + str(self.ndsi_pass2) + ")" \
                                  + " and (im1b" + str(self.nRed) + ">" + str(self.rRed_pass2) + ")"

                bandMathPass2 = band_math([self.img,
                                           self.dem,
                                           self.cloud_refine_path],
                                          self.pass2_path + GDAL_OPT,
                                          condition_pass2 + "?1:0",
                                          self.ram,
                                          otb.ImagePixelType_uint8)

                bandMathPass2.ExecuteAndWriteOutput()
                bandMathPass2 = None

                if self.generate_intermediate_vectors:
                    # Generate polygons for pass2 (useful for quality check)
                    # TODO
                    polygonize(self.pass2_path,
                               self.pass2_path,
                               op.join(self.path_tmp, "pass2_vec.shp"),
                               self.use_gdal_trace_outline,
                               self.gdal_trace_outline_min_area,
                               self.gdal_trace_outline_dp_toler)
                self.pass3()
                generic_snow_path = self.pass3_path
            else:
                # No zs elevation found, take result of pass1 in the output
                # product
                logging.warning("did not find zs, keep pass 1 result.")
                generic_snow_path = self.pass1_path
                # empty image pass2 is needed for computing snow_all

                bandMathEmptyPass2 = band_math([self.pass1_path],
                                               self.pass2_path + GDAL_OPT,
                                               "0",
                                               self.ram,
                                               otb.ImagePixelType_uint8)
                bandMathEmptyPass2.ExecuteAndWriteOutput()

        else:
            generic_snow_path = self.pass1_path
            # empty image pass2 is needed for computing snow_all
            # FIXME: A bit overkill to need to BandMath to create an image with
            # 0
            bandMathEmptyPass2 = band_math([self.pass1_path],
                                           self.pass2_path + GDAL_OPT,
                                           "0",
                                           self.ram,
                                           otb.ImagePixelType_uint8)
            bandMathEmptyPass2.ExecuteAndWriteOutput()

        if self.generate_intermediate_vectors:
            # Generate polygons for pass3 (useful for quality check)
            polygonize(generic_snow_path,
                       generic_snow_path,
                       op.join(self.path_tmp, "pass3_vec.shp"),
                       self.use_gdal_trace_outline,
                       self.gdal_trace_outline_min_area,
                       self.gdal_trace_outline_dp_toler)

        # Final update of the snow  mask (include snow/nosnow/cloud)

        ## Strict cloud mask checking
        if self.strict_cloud_mask:
            logging.info("Strict cloud masking of snow pixels.")
            logging.info("Only keep snow pixels which are not in the initial cloud mask in the final mask.")
            if self.mode == 'sen2cor':
                logging.info("With sen2cor, strict cloud masking corresponds to the default configuration.")
            condition_snow = "(im2b1==1) and (im3b1==0)"
        else:
            condition_snow = "(im2b1==1)"

        condition_final = condition_snow + "?" + str(self.label_snow) + \
                          ":((im1b1==1) or (im3b1==1))?"+str(self.label_cloud)+":0"

        logging.info("Final condition for snow masking: " + condition_final)

        bandMathFinalCloud = band_math([self.cloud_refine_path,
                                        generic_snow_path,
                                        self.mask_backtocloud],
                                       self.final_mask_path,
                                       condition_final,
                                       self.ram,
                                       otb.ImagePixelType_uint8)
        bandMathFinalCloud.ExecuteAndWriteOutput()
        bandMathFinalCloud = None

        # Apply the no-data mask
        bandMathNoData = band_math([self.final_mask_path,
                                    self.nodata_path],
                                   self.final_mask_path,
                                   "im2b1==1?"+str(self.label_no_data)+":im1b1",
                                   self.ram,
                                   otb.ImagePixelType_uint8)
        bandMathNoData.ExecuteAndWriteOutput()
        bandMathNoData = None

        # Compute the complete snow mask
        app = compute_snow_mask(self.pass1_path,
                                self.pass2_path,
                                self.cloud_pass1_path,
                                self.cloud_refine_path,
                                self.all_cloud_path,
                                self.snow_all_path,
                                self.slope_mask_path,
                                self.ram,
                                otb.ImagePixelType_uint8)
        app.ExecuteAndWriteOutput()

    def pass3(self):
        # Fuse pass1 and pass2
        condition_pass3 = "(im1b1 == 1 or im2b1 == 1)"
        bandMathPass3 = band_math([self.pass1_path,
                                   self.pass2_path],
                                  self.pass3_path + GDAL_OPT,
                                  condition_pass3 + "?1:0",
                                  self.ram,
                                  otb.ImagePixelType_uint8)
        bandMathPass3.ExecuteAndWriteOutput()
