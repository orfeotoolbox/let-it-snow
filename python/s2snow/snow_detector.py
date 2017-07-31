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
    gdal_trace_outline_path = None
    if gdal_trace_outline_path is None:
        # Use gdal_polygonize
        call_subprocess([
        "gdal_polygonize.py", input_img,
        "-f", "ESRI Shapefile",
        "-mask", input_mask, output_vec])
    else:
        loggging.info("Use gdal_trace_outline to polygonize raster mask...")

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

    # 2) rasterize cloud and cloud shadows polygon borders in green
    call_subprocess(["gdal_rasterize",
                     "-b",
                     "1",
                     "-b",
                     "2",
                     "-b",
                     "3",
                     "-burn",
                     "0",
                     "-burn",
                     "255",
                     "-burn",
                     "0",
                     "-where",
                     'DN=2',
                     "-l",
                     str(unique_filename),
                     tmp_line + ".shp",
                     input_img])
    # FIXME can't find the right syntax here to use gdal lib
    logging.info("gdal.Rasterize : ")
    logging.info("input = " + input_img)
    logging.info("shapefile = " + tmp_line+".shp")
    logging.info("layers = " + str(unique_filename))
    # gdal.Rasterize(input_img , tmp_line+".shp" , bands = [1,2,3] , burnValues = [0,255,0] , where='DN=2', layers = str(unique_filename) )
    # 3) rasterize snow polygon borders in magenta
    call_subprocess(["gdal_rasterize",
                     "-b",
                     "1",
                     "-b",
                     "2",
                     "-b",
                     "3",
                     "-burn",
                     "255",
                     "-burn",
                     "0",
                     "-burn",
                     "255",
                     "-where",
                     'DN=1',
                     "-l",
                     str(unique_filename),
                     tmp_line + ".shp",
                     input_img])
    # FIXME can't find the right syntax here to use gdal lib
    #gdal.Rasterize(input_img , tmp_line+".shp" , bands = [1,2,3] , burnValues = [255,0,255] , where='DN=1' , layers = str(unique_filename) )

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
        logging.info("il = " + ";".join(il))
        logging.info("out = " + out)
        logging.info("exp = " + exp)

        bandMathApp = otb.Registry.CreateApplication("BandMath")
        bandMathApp.SetParameterString("exp", exp)
        bandMathApp.SetParameterStringList("il", il)
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
        self.do_postprocessing = True
        self.nodata = -10000  # TODO parse json if needed
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

        # Gdal polygonize (needed to produce composition)
        # TODO: Study possible loss and issue with vectorization product
        polygonize(
            op.join(self.path_tmp, "final_mask.tif"),
            op.join(self.path_tmp, "final_mask.tif"),
            op.join(self.path_tmp, "final_mask_vec.shp"))

        # RGB composition
        composition_RGB(
            self.img,
            op.join(self.path_tmp, "composition.tif"),
            self.nSWIR,
            self.nRed,
            self.nGreen,
            self.multi)

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
        call_subprocess([
            "compute_cloud_mask",
            self.cloud_init,
            str(self.all_cloud_mask),
            op.join(self.path_tmp, "all_cloud_mask.tif")])

        # Extract shadow masks
        # First extract shadow wich corresponds to shadow of clouds inside the
        # image
        call_subprocess([
            "compute_cloud_mask",
            self.cloud_init,
            str(self.shadow_in_mask),
            op.join(self.path_tmp, "shadow_in_mask.tif")])

        # Then extract shadow mask of shadows from clouds outside the image
        call_subprocess([
            "compute_cloud_mask",
            self.cloud_init,
            str(self.shadow_out_mask),
            op.join(self.path_tmp, "shadow_out_mask.tif")])

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
        # FIXME Replace with an OTB Application and then call with Python API
        call_subprocess(["compute_cloud_mask", self.cloud_init, str(
            self.high_cloud_mask), op.join(self.path_tmp, "high_cloud_mask.tif")])

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
        self.zs = histo_utils_ext.compute_snowline(self.dem, self.ndsi_pass1_path, op.join(
            self.path_tmp, "cloud_pass1.tif"), self.dz, self.fsnow_lim, False, -2, -self.dz / 2, histo_log)

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
                    polygonize(
                        op.join(
                            self.path_tmp, "pass2.tif"), op.join(
                            self.path_tmp, "pass2.tif"), op.join(
                            self.path_tmp, "pass2_vec.shp"))
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
            polygonize(
                generic_snow_path,
                generic_snow_path,
                op.join(
                    self.path_tmp,
                    "pass3_vec.shp"))

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

        # FIXME Replace with an OTB Application and call to the OTB Application
        # Python API
        call_subprocess(
            [
                "compute_snow_mask", op.join(
                    self.path_tmp, "pass1.tif"), op.join(
                    self.path_tmp, "pass2.tif"), op.join(
                    self.path_tmp, "cloud_pass1.tif"), op.join(
                        self.path_tmp, "cloud_refine.tif"), op.join(
                            self.path_tmp, "snow_all.tif")])

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

    def sentinel_2_preprocessing(self):
        # Handle Sentinel-2 case here. Sentinel-2 images are in 2 separates tif. R1
        #(green/red) at 10 meters and R2 (swir) at 20 meters. Need to extract each
        # band separately and resample green/red to 20 meters.

        # Index of bands in R1 and R2 respectively
        nGreen = 2
        nSWIR = 5
        nRed = 3
        nodata = -10000

        if not os.path.isdir(self.img):
            sys.exit("Sentinel-2 image path must be a directory!")

        # Build sentinel-2 image product path using Level2-a theia product
        # specification. Using FRE images to get slope correction products.
        s2_r1_img_path = glob.glob(op.join(self.img, "*FRE_R1*.TIF"))
        s2_r2_img_path = glob.glob(op.join(self.img, "*FRE_R2*.TIF"))

        if not s2_r1_img_path:
            sys.exit("No R1 S2 image found in Sentinel-2 directory.")

        if not s2_r2_img_path:
            sys.exit("No R2 S2 image found in Sentinel-2 directory.")

        # Build in path for extracted and resampled (20 merters) green band
        greenBand_path = op.join(self.path_tmp, "green_s2.tif")
        greenBand_resample_path = op.join(
            self.path_tmp, "s2_green_resample.tif")

        # Build in path for extracted and resampled (20 merters) green band
        redBand_path = op.join(self.path_tmp, "red_s2.tif")
        redBand_resample_path = op.join(self.path_tmp, "s2_red_resample.tif")

        # Path for swir band (already at 20 meters)
        swirBand_path = op.join(self.path_tmp, "swir_s2.tif")

        # Extract green bands and resample to 20 meters
        # FIXME Use multi resolution pyramid application or new resampling
        # filter fontribute by J. Michel hear
        gdal.Translate(
            greenBand_path,
            s2_r1_img_path[0],
            format='GTiff',
            outputType=gdal.GDT_Int16,
            noData=self.nodata,
            bandList=[nGreen])
        gdal.Warp(
            greenBand_resample_path,
            greenBand_path,
            resampleAlg=gdal.GRIORA_Cubic,
            xRes=20,
            yRes=20)

        # Extract red bands and sample to 20 meters
        # FIXME Use multi resolution pyramid application or new resampling
        # filter fontribute by J. Michel hear
        gdal.Translate(
            redBand_path,
            s2_r1_img_path[0],
            format='GTiff',
            outputType=gdal.GDT_Int16,
            noData=self.nodata,
            bandList=[nRed])
        gdal.Warp(
            redBand_resample_path,
            redBand_path,
            resampleAlg=gdal.GRIORA_Cubic,
            xRes=20,
            yRes=20)

        # Extract SWIR
        gdal.Translate(
            swirBand_path,
            s2_r2_img_path[0],
            format='GTiff',
            outputType=gdal.GDT_Int16,
            noData=self.nodata,
            bandList=[nSWIR])

        # Concatenate all bands in a single image
        concat_s2 = op.join(path_tmp, "concat_s2.tif")

        Concatenate = otb.Registry.CreateApplication("ConcatenateImages")

        Concatenate.SetParameterStringList("il", [greenBand_resample_path,
                                                  redBand_resample_path,
                                                  swirBand_path])
        Concatenate.SetParameterString("ram", str(ram))
        Concatenate.SetParameterString("out", concat_s2)
        Concatenate.SetParameterOutputImagePixelType(
            "out", otb.ImagePixelType_int16)

        Concatenate.ExecuteAndWriteOutput()

        # img variable is used later to compute snow mask
        self.img = concat_s2
        self.redBand_path = op.join(path_tmp, "red.tif")
