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

import sys
import subprocess
import glob
import os
import os.path as op
import json
import logging
import gdal
from gdalconst import *
import multiprocessing
import numpy as np
import uuid
from shutil import copyfile
from distutils import spawn
# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

# Internal C++ lib to compute histograms and minimum elevation threshold
# (step 2)
import histo_utils_ext

# Preprocessing an postprocessing script
import dem_builder
import format_output

# OTB Applications
import otbApplication as otb

# Build gdal option to generate maks of 1 byte using otb extended filename
# syntaxx
GDAL_OPT = "?&gdal:co:NBITS=1&gdal:co:COMPRESS=DEFLATE"

# Build gdal option to generate maks of 2 bytes using otb extended filename
# syntax
GDAL_OPT_2B = "?&gdal:co:NBITS=2&gdal:co:COMPRESS=DEFLATE"


def call_subprocess(process_list):
    """ Run subprocess and write to stdout and stderr
    """
    logging.info("Running: " + " ".join(process_list))
    process = subprocess.Popen(
        process_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = process.communicate()
    logging.info(out)
    sys.stderr.write(err)


def polygonize(input_img, input_mask, output_vec):
    """Helper function to polygonize raster mask using gdal polygonize

    if gina-tools is available it use gdal_trace_outline instead of
    gdal_polygonize (faster)
    """
    # Test if gdal_trace_outline is available
    gdal_trace_outline_path = spawn.find_executable("gdal_trace_outline")
    if gdal_trace_outline_path is None:
        # Use gdal_polygonize
        call_subprocess([
        "gdal_polygonize.py", input_img,
        "-f", "ESRI Shapefile",
        "-mask", input_mask, output_vec])
    else:
        logging.info("Use gdal_trace_outline to polygonize raster mask...")

        # Temporary file to store result of outline tool
        # Get unique identifier for the temporary file
        # Retrieve directory from input vector file
        input_dir = os.path.dirname(output_vec)
        unique_filename = uuid.uuid4()
        tmp_poly = op.join(input_dir, str(unique_filename))

        tmp_poly_shp = tmp_poly + ".shp"
        # We can use here gina-tools gdal_trace_outline which is faster
        call_subprocess([
            "gdal_trace_outline",
             input_img,
             "-classify",
             "-out-cs",
             "en",
             "-ogr-out",
             tmp_poly_shp,
             "-dp-toler",
             "0",
             "-split-polys"])

        # Then remove polygons with 0 as field value and rename field from
        # "value" to "DN" to follow same convention as gdal_polygonize
        call_subprocess([
            "ogr2ogr",
            "-sql",
            'SELECT value AS DN from \"' +
            str(unique_filename) +
            '\" where value != 0',
            output_vec,
            tmp_poly_shp])

        # Remove temporary vectors
        for shp in glob.glob(tmp_poly + "*"):
            os.remove(shp)


def composition_RGB(input_img, output_img, nSWIR, nRed, nGreen, multi):
    """Make a RGB composition to highlight the snow cover

    input_img: multispectral tiff, output_img: false color
    composite RGB image (GTiff).nRed,nGreen,nSWIR are index of red, green and
    SWIR in in put images.

    """
    scale_factor = 300 * multi

    gdal.Translate(output_img,
                   input_img,
                   format='GTiff',
                   creationOptions=['PHOTOMETRIC=RGB'],
                   outputType=gdal.GDT_Byte,
                   scaleParams=[[0,
                                 scale_factor,
                                 0,
                                 255]],
                   bandList=[nSWIR,
                             nRed,
                             nGreen])


def burn_polygons_edges(input_img, input_vec):
    """Burn polygon borders onto an image with the following symbology:

    - cloud and cloud shadows: green
    - snow: magenta
    - convert mask polygons to lines

    """

    # Save temporary file in working directory

    # Retrieve directory from input vector file
    input_dir = os.path.dirname(input_vec)
    # TODO move to snowdetector class?
    # Get unique identifier for the temporary file
    unique_filename = uuid.uuid4()
    tmp_line = op.join(input_dir, str(unique_filename))
    logging.info("tmpline: " + str(tmp_line))

    gdal.VectorTranslate(
        tmp_line + ".shp",
        input_vec,
        accessMode='overwrite',
        geometryType='MULTILINESTRING')

    logging.info("gdal.Rasterize inputs: ")
    logging.info("input = " + input_img)
    logging.info("shapefile = " + tmp_line+".shp")
    logging.info("layers = " + str(unique_filename))

    # Warning: We have to open the input_img (filename) as img_ds (dataset)
    # the gdal.Rasterize method return a segfault when using directly input_img
    img_ds=gdal.Open(input_img, gdal.GA_Update)

    # 2) rasterize cloud and cloud shadows polygon borders in green
    gdal.Rasterize(img_ds,
                   tmp_line+".shp",
                   bands=[1,2,3],
                   burnValues=[0,255,0],
                   where='DN=2',
                   layers=str(unique_filename))

    # 3) rasterize snow polygon borders in magenta
    gdal.Rasterize(img_ds,
                   tmp_line+".shp",
                   bands=[1,2,3],
                   burnValues=[255,0,255],
                   where='DN=1',
                   layers=str(unique_filename))

    # 4) remove tmp_line files
    for shp in glob.glob(tmp_line + "*"):
        os.remove(shp)

def extract_band(inputs, band, path_tmp, noData):
    """ Extract the required band using gdal.Translate
    """
    data_band = inputs[band]
    path = data_band["path"]
    band_no = data_band["noBand"]

    dataset = gdal.Open(path, GA_ReadOnly)
    path_extracted = op.join(path_tmp, band+"_extracted.tif")
    if dataset.RasterCount > 1:
        logging.info("extracting "+band)
        gdal.Translate(
            path_extracted,
            path,
            format='GTiff',
            outputType=gdal.GDT_Int16,
            noData=noData,
            bandList=[band_no])
    else:
        copyfile(path, path_extracted)
    return path_extracted

def band_math(il, out, exp, ram=None, out_type=None):
    """ Create and configure the band math application
        using otb.Registry.CreateApplication("BandMath")

    Keyword arguments:
    il -- the input image list
    out -- the output image
    exp -- the math expression
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if il and out and exp:
        logging.info("Processing BandMath with args:")
        logging.info("il = " + ";".join([str(x) for x in il]))
        logging.info("out = " + out)
        logging.info("exp = " + exp)

        bandMathApp = otb.Registry.CreateApplication("BandMath")
        bandMathApp.SetParameterString("exp", exp)
        for image in il:
            if isinstance(image, basestring):
                bandMathApp.AddParameterStringList("il",image)
            else:
                bandMathApp.AddImageToParameterInputImageList("il",image)
        bandMathApp.SetParameterString("out", out)

        if ram is not None:
            logging.info("ram = " + str(ram))
            bandMathApp.SetParameterString("ram", str(ram))
        if out_type is not None:
            logging.info("out_type = " + str(out_type))
            bandMathApp.SetParameterOutputImagePixelType("out", out_type)
        return bandMathApp
    else:
        logging.error("Parameters il, out and exp are required")

def compute_cloud_mask(img_in, img_out, cloudmaskvalue, ram=None, out_type=None):
    """ Create and configure the Compute Cloud Mask application
        using otb.Registry.CreateApplication("ComputeCloudMask")

    Keyword arguments:
    img_in -- the input image
    img_out -- the output image
    cloudmaskvalue -- the value corresponding to cloud
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if img_in and img_out and cloudmaskvalue:
        logging.info("Processing ComputeCloudMask with args:")
        logging.info("in = " + img_in)
        logging.info("out = " + img_out)
        logging.info("cloudmaskvalue = " + cloudmaskvalue)

        cloudMaskApp = otb.Registry.CreateApplication("ComputeCloudMask")
        cloudMaskApp.SetParameterString("cloudmaskvalue", cloudmaskvalue)
        cloudMaskApp.SetParameterString("in", img_in)
        cloudMaskApp.SetParameterString("out", img_out)
        if ram is not None:
            logging.info("ram = " + str(ram))
            cloudMaskApp.SetParameterString("ram", str(ram))
        if out_type is not None:
            logging.info("out_type = " + str(out_type))
            cloudMaskApp.SetParameterOutputImagePixelType("out", out_type)
        return cloudMaskApp
    else:
        logging.error("Parameters img_in, img_out and cloudmaskvalue are required")

def compute_snow_mask(pass1, pass2, cloud_pass1, cloud_refine, out, ram=None, out_type=None):
    """ Create and configure the Compute Cloud Snow application
        using otb.Registry.CreateApplication("ComputeSnowMask")

    Keyword arguments:
    pass1 -- the input pass1 image
    pass2 -- the input pass2 image
    cloud_pass1 -- the input cloud pass1 image
    cloud_refine -- the input cloud refine image
    out -- the output image
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if pass1 and pass2 and cloud_pass1 and cloud_refine and out:
        logging.info("Processing ComputeSnowMask with args:")
        logging.info("pass1 = " + pass1)
        logging.info("pass2 = " + pass2)
        logging.info("cloud_pass1 = " + cloud_pass1)
        logging.info("cloud_refine = " + cloud_refine)
        logging.info("out = " + out)

        snowMaskApp = otb.Registry.CreateApplication("ComputeSnowMask")
        snowMaskApp.SetParameterString("pass1", pass1)
        snowMaskApp.SetParameterString("pass2", pass2)
        snowMaskApp.SetParameterString("cloudpass1", cloud_pass1)
        snowMaskApp.SetParameterString("cloudrefine", cloud_refine)
        snowMaskApp.SetParameterString("out", out)
        if ram is not None:
            logging.info("ram = " + str(ram))
            snowMaskApp.SetParameterString("ram", str(ram))
        if out_type is not None:
            logging.info("out_type = " + str(out_type))
            snowMaskApp.SetParameterOutputImagePixelType("out", out_type)
        return snowMaskApp
    else:
        logging.error("Parameters pass1, pass2, cloud_pass1, cloud_refine and out are required")

class snow_detector:
    def __init__(self, data):

        # Parse general parameters
        general = data["general"]
        self.path_tmp = str(general.get("pout"))
        self.ram = general.get("ram", 512)
        try:
            nbDefaultThreads = multiprocessing.cpu_count()
        except NotImplementedError:
            logging.error("Cannot get max number of CPU on the system. nbDefaultThreads set to 1.")
            nbDefaultThreads = 1
        self.nbThreads = general.get("nbThreads", nbDefaultThreads)
        self.mode = general.get("mode")
        self.generate_vector = general.get("generate_vector", False)
        self.do_preprocessing = general.get("preprocessing", False)
        self.do_postprocessing = general.get("postprocessing", True)
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

        # Parse input parameters
        inputs = data["inputs"]
        if(self.do_preprocessing):
            self.vrt = str(inputs.get("vrt"))
        # self.img=str(inputs.get("image"))
        self.dem = str(inputs.get("dem"))
        self.cloud_init = str(inputs.get("cloud_mask"))

        # bands paths
        gb_path_extracted = extract_band(inputs, "green_band", self.path_tmp, self.nodata)
        rb_path_extracted = extract_band(inputs, "red_band", self.path_tmp, self.nodata)
        sb_path_extracted = extract_band(inputs, "swir_band", self.path_tmp, self.nodata)

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

        # Build useful paths
        self.redBand_path = op.join(self.path_tmp, "red.tif")
        self.ndsi_pass1_path = op.join(self.path_tmp, "pass1.tif")
        self.cloud_refine = op.join(self.path_tmp, "cloud_refine.tif")
        self.nodata_path = op.join(self.path_tmp, "nodata_mask.tif")

    def detect_snow(self, nbPass):
        # Set maximum ITK threads
        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(self.nbThreads)

        # External preprocessing
        if self.do_preprocessing:
            dem_builder.build_dem(self.vrt, self.img, self.dem)

        # Initialize the mask
        noDataMaskExpr = "im1b1==" + str(self.nodata) + "?1:0"
        bandMath = band_math(
            [self.img],
            self.nodata_path,
            noDataMaskExpr,
            self.ram)
        bandMath.ExecuteAndWriteOutput()

        if nbPass >= 0:
            self.pass0()
        if nbPass >= 1:
            self.pass1()
        if nbPass == 2:
            self.pass2()

        # RGB composition
        composition_RGB(
            self.img,
            op.join(self.path_tmp, "composition.tif"),
            self.nSWIR,
            self.nRed,
            self.nGreen,
            self.multi)

        # Gdal polygonize (needed to produce composition)
        # TODO: Study possible loss and issue with vectorization product
        polygonize(
            op.join(self.path_tmp, "final_mask.tif"),
            op.join(self.path_tmp, "final_mask.tif"),
            op.join(self.path_tmp, "final_mask_vec.shp"))

        # Burn polygons edges on the composition
        # TODO add pass1 snow polygon in yellow
        burn_polygons_edges(
            op.join(self.path_tmp, "composition.tif"),
            op.join(self.path_tmp, "final_mask_vec.shp"))

        # External postprocessing
        if self.do_postprocessing:
            format_output.format_LIS(self)

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

        # resample red band using multiresolution pyramid
        gdal.Warp(
            op.join(self.path_tmp,"red_coarse.tif"),
            self.redBand_path,
            resampleAlg=gdal.GRIORA_Bilinear,
            width=xSize / self.rf,
            height=ySize / self.rf)

        # Resample red band nn
        # FIXME: use MACCS resampling filter contribute in OTB 5.6 here
        gdal.Warp(
            op.join(self.path_tmp,"red_nn.tif"),
            op.join(self.path_tmp,"red_coarse.tif"),
            resampleAlg=gdal.GRIORA_NearestNeighbour,
            width=xSize,
            height=ySize)

        # edit result to set the resolution to the input image resolution
        # TODO need to find a better solution and also guess the input spacing
        # (using maccs resampling filter)
        dataset=gdal.Open(op.join(self.path_tmp,"red_nn.tif"),gdal.GA_Update)
        dataset.SetGeoTransform(geotransform)
        dataset=None

        # Extract all masks
        computeCMApp = compute_cloud_mask(self.cloud_init,
                                          op.join(self.path_tmp, "all_cloud_mask.tif"),
                                          str(self.all_cloud_mask))
        computeCMApp.ExecuteAndWriteOutput()

        # Extract shadow masks
        # First extract shadow wich corresponds to shadow of clouds inside the
        # image
        computeCMApp = compute_cloud_mask(self.cloud_init,
                                          op.join(self.path_tmp, "shadow_in_mask.tif"),
                                          str(self.shadow_in_mask))
        computeCMApp.ExecuteAndWriteOutput()

        # Then extract shadow mask of shadows from clouds outside the image
        computeCMApp = compute_cloud_mask(self.cloud_init,
                                          op.join(self.path_tmp, "shadow_out_mask.tif"),
                                          str(self.shadow_out_mask))
        computeCMApp.ExecuteAndWriteOutput()

        # The output shadow mask corresponds to a OR logic between the 2 shadow
        # masks
        bandMathShadow = band_math([
                                op.join(self.path_tmp, "shadow_in_mask.tif"),
                                op.join(self.path_tmp, "shadow_out_mask.tif")],
                                op.join(self.path_tmp, "shadow_mask.tif"),
                                "(im1b1 == 1) || (im2b1 == 1)",
                                self.ram,
                                otb.ImagePixelType_uint8)
        bandMathShadow.ExecuteAndWriteOutput()

        # Extract high clouds
        computeCMApp = compute_cloud_mask(self.cloud_init,
                                          op.join(self.path_tmp, "high_cloud_mask.tif"),
                                          str(self.high_cloud_mask))
        computeCMApp.ExecuteAndWriteOutput()

        cond_cloud2 = "im3b1>" + str(self.rRed_darkcloud)
        condition_shadow = "((im1b1==1 and " + cond_cloud2 + \
            ") or im2b1==1 or im4b1==1)"

        logging.info(condition_shadow)

        bandMathFinalShadow = band_math([op.join(self.path_tmp, "all_cloud_mask.tif"),
                                op.join(self.path_tmp, "shadow_mask.tif"),
                                op.join(self.path_tmp, "red_nn.tif"),
                                op.join(self.path_tmp, "high_cloud_mask.tif")],
                                self.cloud_refine+GDAL_OPT,
                                condition_shadow,
                                self.ram,
                                otb.ImagePixelType_uint8)
        bandMathFinalShadow.ExecuteAndWriteOutput()

    def pass1(self):
        # Pass1 : NDSI threshold
        ndsi_formula = "(im1b" + str(self.nGreen) + "-im1b" + str(self.nSWIR) + \
            ")/(im1b" + str(self.nGreen) + "+im1b" + str(self.nSWIR) + ")"
        logging.info("ndsi formula: "+ ndsi_formula)

        condition_pass1 = "(im2b1!=1 and (" + ndsi_formula + ")>" + str(self.ndsi_pass1) + \
            " and im1b" + str(self.nRed) + "> " + str(self.rRed_pass1) + ")"

        bandMathPass1 = band_math([self.img, self.cloud_refine],
                                self.ndsi_pass1_path + GDAL_OPT,
                                condition_pass1 + "?1:0",
                                self.ram,
                                otb.ImagePixelType_uint8)
        bandMathPass1.ExecuteAndWriteOutput()
        # bandMathPass1.Execute()

        # Update the cloud mask (again)
        condition_cloud_pass1 = "(im1b1==1 or (im2b1!=1 and im3b1==1 and im4b1> " + \
            str(self.rRed_backtocloud) + "))"

        bandMathCloudPass1 = band_math([self.cloud_refine,
                                self.ndsi_pass1_path,
                                self.cloud_init,
                                self.redBand_path],
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
            self.ndsi_pass1_path, 0, 1)
        logging.info("Number of snow pixels =" + str(nb_snow_pixels))

        # Compute Zs elevation fraction and histogram values
        # We compute it in all case as we need to check histogram values to
        # detect cold clouds in optionnal pass4

        histo_log = op.join(self.path_tmp, "histogram.txt")
        #c++ function
        
        logging.info("histo_utils_ext.compute_snowline args:")
        logging.info(self.dem)
        logging.info(self.ndsi_pass1_path)
        logging.info(op.join(self.path_tmp, "cloud_pass1.tif"))
        logging.info(self.dz)
        logging.info(self.fsnow_lim)
        logging.info(histo_log)
        self.zs = histo_utils_ext.compute_snowline(self.dem, 
                                    self.ndsi_pass1_path,
                                    op.join(self.path_tmp, "cloud_pass1.tif"),
                                    self.dz,
                                    self.fsnow_lim,
                                    False,
                                    -2,
                                    -self.dz / 2,
                                    histo_log)

        logging.info("computed ZS:" + str(self.zs))

        if (nb_snow_pixels > self.fsnow_total_lim):
            # Test zs value (-1 means that no zs elevation was found)
            if (self.zs != -1):
                # NDSI threshold again
                condition_pass2 = "(im3b1 != 1) and (im2b1>" + str(self.zs) + ") and (" + ndsi_formula + "> " + str(
                    self.ndsi_pass2) + ") and (im1b" + str(self.nRed) + ">" + str(self.rRed_pass2) + ")"

                bandMathPass2 = band_math([self.img,
                                self.dem,
                                self.cloud_refine],
                                op.join(self.path_tmp, "pass2.tif") + GDAL_OPT,
                                condition_pass2 + "?1:0",
                                self.ram,
                                otb.ImagePixelType_uint8)

                bandMathPass2.ExecuteAndWriteOutput()

                if self.generate_vector:
                    # Generate polygons for pass2 (useful for quality check)
                    # TODO
                    polygonize(op.join(self.path_tmp, "pass2.tif"),
                               op.join(self.path_tmp, "pass2.tif"),
                               op.join(self.path_tmp, "pass2_vec.shp"))
                self.pass3()
                generic_snow_path = op.join(self.path_tmp, "pass3.tif")
            else:
                # No zs elevation found, take result of pass1 in the output
                # product
                logging.warning("did not find zs, keep pass 1 result.")
                generic_snow_path = self.ndsi_pass1_path
                # empty image pass2 is needed for computing snow_all

                bandMathEmptyPass2 = band_math([op.join(self.path_tmp, "pass1.tif")],
                                op.join(self.path_tmp, "pass2.tif") + GDAL_OPT,
                                "0",
                                self.ram,
                                otb.ImagePixelType_uint8)
                bandMathEmptyPass2.ExecuteAndWriteOutput()

        else:
            generic_snow_path = self.ndsi_pass1_path
            # empty image pass2 is needed for computing snow_all
            # FIXME: A bit overkill to need to BandMath to create an image with
            # 0
            bandMathEmptyPass2 = band_math([op.join(self.path_tmp, "pass1.tif")],
                                op.join(self.path_tmp, "pass2.tif") + GDAL_OPT,
                                "0",
                                self.ram,
                                otb.ImagePixelType_uint8)
            bandMathEmptyPass2.ExecuteAndWriteOutput()

        if self.generate_vector:
            # Generate polygons for pass3 (useful for quality check)
            polygonize(generic_snow_path,
                       generic_snow_path,
                       op.join(self.path_tmp,"pass3_vec.shp"))

        # Final update of the cloud mask
        condition_final = "(im2b1==1)?1:((im1b1==1) or ((im3b1>0) and (im4b1> " + \
            str(self.rRed_backtocloud) + ")))?2:0"

        bandMathFinalCloud = band_math([self.cloud_refine,
                            generic_snow_path,
                            self.cloud_init,
                            self.redBand_path],
                            op.join(self.path_tmp, "final_mask.tif") + GDAL_OPT_2B,
                            condition_final,
                            self.ram,
                            otb.ImagePixelType_uint8)
        bandMathFinalCloud.ExecuteAndWriteOutput()

        app = compute_snow_mask(op.join(self.path_tmp, "pass1.tif"),
                                op.join(self.path_tmp, "pass2.tif"),
                                op.join(self.path_tmp, "cloud_pass1.tif"),
                                op.join(self.path_tmp, "cloud_refine.tif"),
                                op.join(self.path_tmp, "snow_all.tif"),
                                out_type=otb.ImagePixelType_uint8)
        app.ExecuteAndWriteOutput()

    def pass3(self):
        # Fuse pass1 and pass2
        condition_pass3 = "(im1b1 == 1 or im2b1 == 1)"
        bandMathPass3 = band_math([self.ndsi_pass1_path,
                                   op.join(self.path_tmp,"pass2.tif")],
                                   op.join(self.path_tmp, "pass3.tif") + GDAL_OPT,
                                   condition_pass3 + "?1:0",
                                   self.ram,
                                   otb.ImagePixelType_uint8)
        bandMathPass3.ExecuteAndWriteOutput()
