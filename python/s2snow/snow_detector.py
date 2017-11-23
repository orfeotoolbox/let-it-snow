#!/usr/bin/python
# coding=utf8
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
import logging
import multiprocessing
from lxml import etree

import gdal
from gdalconst import GA_ReadOnly

# OTB Applications
import otbApplication as otb

# Internal C++ lib to compute histograms and minimum elevation threshold
# (step 2)
import histo_utils_ext

# Preprocessing script
from s2snow.dem_builder import build_dem

# Import python decorators for the different needed OTB applications
from s2snow.app_wrappers import compute_snow_mask, compute_cloud_mask, band_math

# Import utilities for snow detection
from s2snow.utils import polygonize, extract_band, burn_polygons_edges, composition_RGB
from s2snow.utils import compute_percent, format_SEB_VEC_values

# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

# Build gdal option to generate maks of 1 byte using otb extended filename
# syntaxx
GDAL_OPT = "?&gdal:co:NBITS=1&gdal:co:COMPRESS=DEFLATE"

# Build gdal option to generate maks of 2 bytes using otb extended filename
# syntax
GDAL_OPT_2B = "?&gdal:co:NBITS=2&gdal:co:COMPRESS=DEFLATE"


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
        self.generate_vector = general.get("generate_vector", False)
        self.do_preprocessing = general.get("preprocessing", False)
        self.nodata = general.get("nodata", -10000)
        self.multi = general.get("multi", 1)  # Multiplier to handle S2 scaling

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
        
        # Parse input parameters
        inputs = data["inputs"]
        if self.do_preprocessing:
            self.vrt = str(inputs.get("vrt"))
        # self.img=str(inputs.get("image"))
        self.dem = str(inputs.get("dem"))
        self.cloud_init = str(inputs.get("cloud_mask"))

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
        if not gb_resolution == rb_resolution == sb_resolution:
            logging.info("resolution is different among band files")
            # gdalwarp to max reso
            max_res = max(gb_resolution, rb_resolution, sb_resolution)
            logging.info("cubic resampling to " + str(max_res) + " meters.")

            gdal.Warp(
                gb_path_resampled,
                gb_path_extracted,
                resampleAlg=gdal.GRIORA_Cubic,
                xRes=max_res,
                yRes=max_res)
            gdal.Warp(
                rb_path_resampled,
                rb_path_extracted,
                resampleAlg=gdal.GRIORA_Cubic,
                xRes=max_res,
                yRes=max_res)
            gdal.Warp(
                sb_path_resampled,
                sb_path_extracted,
                resampleAlg=gdal.GRIORA_Cubic,
                xRes=max_res,
                yRes=max_res)
        else:
            gb_path_resampled = gb_path_extracted
            rb_path_resampled = rb_path_extracted
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
        self.cloud_refine_path = op.join(self.path_tmp, "cloud_refine.tif")
        self.nodata_path = op.join(self.path_tmp, "nodata_mask.tif")

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
            build_dem(self.vrt, self.img, self.dem)

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
        polygonize(
            self.final_mask_path,
            self.final_mask_path,
            self.final_mask_vec_path)

        # Burn polygons edges on the composition
        # TODO add pass1 snow polygon in yellow
        burn_polygons_edges(
            self.composition_path,
            self.final_mask_path,
            self.label_snow,
            self.label_cloud,
            self.ram)

        # Product formating
        format_SEB_VEC_values(self.final_mask_vec_path,
                              self.label_snow,
                              self.label_cloud,
                              self.label_no_data)
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
        # FIXME: use MACCS resampling filter contribute in OTB 5.6 here
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

        # Extract all masks
        computeCMApp = compute_cloud_mask(
            self.cloud_init,
            op.join(self.path_tmp, "all_cloud_mask.tif") + GDAL_OPT,
            str(self.all_cloud_mask),
            self.ram,
            otb.ImagePixelType_uint8)
        computeCMApp.ExecuteAndWriteOutput()
        computeCMApp = None

        # Extract shadow masks
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
            op.join(self.path_tmp, "shadow_mask.tif")+GDAL_OPT,
            "(im1b1 == 1) || (im2b1 == 1)",
            self.ram,
            otb.ImagePixelType_uint8)
        bandMathShadow.ExecuteAndWriteOutput()
        bandMathShadow = None

        # Extract high clouds
        computeCMApp = compute_cloud_mask(
            self.cloud_init,
            op.join(self.path_tmp, "high_cloud_mask.tif") + GDAL_OPT,
            str(self.high_cloud_mask),
            self.ram,
            otb.ImagePixelType_uint8)
        computeCMApp.ExecuteAndWriteOutput()
        computeCMApp = None

        cond_cloud2 = "im3b1>" + str(self.rRed_darkcloud)
        condition_shadow = "((im1b1==1 and " + cond_cloud2 + \
            ") or im2b1==1 or im4b1==1)"

        logging.info(condition_shadow)

        bandMathFinalShadow = band_math(
            [op.join(self.path_tmp, "all_cloud_mask.tif"),
             op.join(self.path_tmp, "shadow_mask.tif"),
             op.join(self.path_tmp, "red_nn.tif"),
             op.join(self.path_tmp, "high_cloud_mask.tif")],
            self.cloud_refine_path + GDAL_OPT,
            condition_shadow,
            self.ram,
            otb.ImagePixelType_uint8)
        bandMathFinalShadow.ExecuteAndWriteOutput()

    def pass1(self):
        # Pass1 : NDSI threshold
        ndsi_formula = "(im1b" + str(self.nGreen) + "-im1b" + str(self.nSWIR) + \
            ")/(im1b" + str(self.nGreen) + "+im1b" + str(self.nSWIR) + ")"
        logging.info("ndsi formula: "+ ndsi_formula)

        # NDSI condition (ndsi > x and not cloud_refine)
        condition_ndsi = "(im2b1!=1 and (" + ndsi_formula + ")>" + str(self.ndsi_pass1) + " "

        condition_pass1 = condition_ndsi + \
            " and im1b" + str(self.nRed) + "> " + str(self.rRed_pass1) + ")"

        bandMathPass1 = band_math(
            [self.img, self.cloud_refine_path, op.join(self.path_tmp, "all_cloud_mask.tif")],
            self.pass1_path + GDAL_OPT,
            condition_pass1 + "?1:0",
            self.ram,
            otb.ImagePixelType_uint8)
        bandMathPass1.ExecuteAndWriteOutput()
        bandMathPass1 = None

        # Update the cloud mask (again)
        condition_cloud_pass1 = "(im1b1==1 or (im2b1!=1 and im3b1==1 and im4b1> " + \
            str(self.rRed_backtocloud) + "))"

        bandMathCloudPass1 = band_math(
            [self.cloud_refine_path, self.pass1_path,
             self.cloud_init, self.redBand_path],
            op.join(self.path_tmp, "cloud_pass1.tif") + GDAL_OPT,
            condition_cloud_pass1 + "?1:0",
            self.ram,
            otb.ImagePixelType_uint8)
        bandMathCloudPass1.ExecuteAndWriteOutput()

    def pass2(self):
        ndsi_formula = "(im1b" + str(self.nGreen) + "-im1b" + str(self.nSWIR) + \
            ")/(im1b" + str(self.nGreen) + "+im1b" + str(self.nSWIR) + ")"
        # Pass 2: compute snow fraction (c++)
        # FIXME: use np.count here ?
        nb_snow_pixels = histo_utils_ext.compute_nb_pixels_between_bounds(
            self.pass1_path, 0, 1)
        logging.info("Number of snow pixels =" + str(nb_snow_pixels))

        # Compute Zs elevation fraction and histogram values
        # We compute it in all case as we need to check histogram values to
        # detect cold clouds in optionnal pass4

        #c++ function
        logging.info("histo_utils_ext.compute_snowline args:")
        logging.info(self.dem)
        logging.info(self.pass1_path)
        logging.info(op.join(self.path_tmp, "cloud_pass1.tif"))
        logging.info(self.dz)
        logging.info(self.fsnow_lim)
        logging.info(self.histogram_path)
        self.zs = histo_utils_ext.compute_snowline(
            self.dem,
            self.pass1_path,
            op.join(self.path_tmp, "cloud_pass1.tif"),
            self.dz,
            self.fsnow_lim,
            False,
            -2,
            -self.dz / 2,
            self.histogram_path)

        logging.info("computed ZS:" + str(self.zs))

        if nb_snow_pixels > self.fsnow_total_lim:
            # Test zs value (-1 means that no zs elevation was found)
            if self.zs != -1:
                # NDSI threshold again
                condition_pass2 = "(im3b1 != 1) and (im2b1>" + str(self.zs) + ") and (" + ndsi_formula + "> " + str(
                    self.ndsi_pass2) + ") and (im1b" + str(self.nRed) + ">" + str(self.rRed_pass2) + ")"

                bandMathPass2 = band_math([self.img,
                                           self.dem,
                                           self.cloud_refine_path],
                                          self.pass2_path + GDAL_OPT,
                                          condition_pass2 + "?1:0",
                                          self.ram,
                                          otb.ImagePixelType_uint8)

                bandMathPass2.ExecuteAndWriteOutput()
                bandMathPass2 = None

                if self.generate_vector:
                    # Generate polygons for pass2 (useful for quality check)
                    # TODO
                    polygonize(self.pass2_path,
                               self.pass2_path,
                               op.join(self.path_tmp, "pass2_vec.shp"))
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

        if self.generate_vector:
            # Generate polygons for pass3 (useful for quality check)
            polygonize(generic_snow_path,
                       generic_snow_path,
                       op.join(self.path_tmp, "pass3_vec.shp"))

        # Final update of the snow  mask (include snow/nosnow/cloud)

        ## Strict cloud mask checking
        logging.info("Strict cloud masking of snow pixels :")
        logging.info(self.strict_cloud_mask)
        if self.strict_cloud_mask == True:
            logging.info("Only keep snow pixels which are not in the initial cloud mask in the final mask.")
            condition_snow = "(im2b1==1) and (im3b1==0)"
        else:
            condition_snow = "(im2b1==1)"

        logging.info("condition snow " + condition_snow)
        
        condition_final = condition_snow + "?"+str(self.label_snow)+":((im1b1==1) or ((im3b1>0) and (im4b1> " + \
            str(self.rRed_backtocloud) + ")))?"+str(self.label_cloud)+":0"

        bandMathFinalCloud = band_math([self.cloud_refine_path,
                                        generic_snow_path,
                                        self.cloud_init,
                                        self.redBand_path],
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
                                op.join(self.path_tmp, "cloud_pass1.tif"),
                                self.cloud_refine_path,
                                self.snow_all_path,
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
