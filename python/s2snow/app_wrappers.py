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
import logging

# OTB Applications
import otbApplication as otb

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
            if isinstance(image, str):
                bandMathApp.AddParameterStringList("il", image)
            else:
                bandMathApp.AddImageToParameterInputImageList("il", image)
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

def compute_cloud_mask(img_in, img_out, cloudmaskvalue, \
                    ram=None, out_type=None):
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
        logging.error("Parameters img_in, img_out \
                       and cloudmaskvalue are required")

def compute_snow_mask(pass1, pass2, cloud_pass1, cloud_refine, initial_clouds, \
                      out, slope_flag=None, ram=None, out_type=None):
    """ Create and configure the Compute Cloud Snow application
        using otb.Registry.CreateApplication("ComputeSnowMask")

    Keyword arguments:
    pass1 -- the input pass1 image
    pass2 -- the input pass2 image
    cloud_pass1 -- the input cloud pass1 image
    cloud_refine -- the input cloud refine image
    initial_clouds -- the inital all cloud image
    out -- the output image
    slope_flag -- the status of the slope
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if pass1 and pass2 and cloud_pass1 and cloud_refine and out:
        logging.info("Processing ComputeSnowMask with args:")
        logging.info("pass1 = " + pass1)
        logging.info("pass2 = " + pass2)
        logging.info("cloud_pass1 = " + cloud_pass1)
        logging.info("cloud_refine = " + cloud_refine)
        logging.info("initial_clouds = " + initial_clouds)
        logging.info("out = " + out)

        snowMaskApp = otb.Registry.CreateApplication("ComputeSnowMask")
        snowMaskApp.SetParameterString("pass1", pass1)
        snowMaskApp.SetParameterString("pass2", pass2)
        snowMaskApp.SetParameterString("cloudpass1", cloud_pass1)
        snowMaskApp.SetParameterString("cloudrefine", cloud_refine)
        snowMaskApp.SetParameterString("initialallcloud", initial_clouds)
        snowMaskApp.SetParameterString("out", out)
        if slope_flag is not None:
            logging.info("slope_flag = " + slope_flag)
            snowMaskApp.SetParameterString("slopeflag", slope_flag)
        if ram is not None:
            logging.info("ram = " + str(ram))
            snowMaskApp.SetParameterString("ram", str(ram))
        if out_type is not None:
            logging.info("out_type = " + str(out_type))
            snowMaskApp.SetParameterOutputImagePixelType("out", out_type)
        return snowMaskApp
    else:
        logging.error("Parameters pass1, pass2, cloud_pass1, \
                       cloud_refine, initial_clouds and out are required")

def band_mathX(il, out, exp, ram=None, out_type=None):
    """ Create and configure the band math application
        using otb.Registry.CreateApplication("BandMathX")

    Keyword arguments:
    il -- the input image list
    out -- the output image
    exp -- the math expression
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if il and out and exp:
        logging.info("Processing BandMathX with args:")
        logging.info("il = " + ";".join([str(x) for x in il]))
        logging.info("out = " + out)
        logging.info("exp = " + exp)

        bandMathApp = otb.Registry.CreateApplication("BandMathX")
        bandMathApp.SetParameterString("exp", exp)
        for image in il:
            if isinstance(image, str):
                bandMathApp.AddParameterStringList("il", image)
            else:
                bandMathApp.AddImageToParameterInputImageList("il", image)
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

def compute_snow_line(img_dem, img_snow, img_cloud, dz, fsnowlim, fclearlim, \
                      reverse, offset, centeroffset, outhist, ram=None):
    """ Create and configure the ComputeSnowLine application
        using otb.Registry.CreateApplication("ComputeSnowLine")

    Keyword arguments:
    TODO
    """
    if img_dem and img_snow and img_cloud:
        logging.info("Processing ComputeSnowLine with args:")
        logging.info(img_dem)
        logging.info(img_snow)
        logging.info(img_cloud)
        logging.info(dz)
        logging.info(fsnowlim)
        logging.info(outhist)

        snowLineApp = otb.Registry.CreateApplication("ComputeSnowLine")
        snowLineApp.SetParameterString("dem", img_dem)
        snowLineApp.SetParameterString("ins", img_snow)
        snowLineApp.SetParameterString("inc", img_cloud)
        snowLineApp.SetParameterString("outhist", outhist)

        # Scalar parameter
        snowLineApp.SetParameterInt("dz", dz)
        snowLineApp.SetParameterFloat("fsnowlim", fsnowlim)
        snowLineApp.SetParameterFloat("fclearlim", fclearlim)
        snowLineApp.SetParameterInt("offset", offset)
        if not isinstance(centeroffset, int):
            if round(centeroffset,0) != centeroffset:
                raise IOError("centeroffset shoud be an integer, got %s instead with value %s => error"%(type(centeroffset), centeroffset))
            else:
                print("WARNING: centeroffset shoud be an integer, got %s instead with value %s => converting to int"%(type(centeroffset), centeroffset))
            centeroffset = int(centeroffset)
        snowLineApp.SetParameterInt("centeroffset", centeroffset)
        if reverse:
            snowLineApp.SetParameterInt("reverse", 1)
        else:
            snowLineApp.SetParameterInt("reverse", 0)

        if ram is not None:
            logging.info("ram = " + str(ram))
            snowLineApp.SetParameterString("ram", str(ram))

        return snowLineApp
    else:
        logging.error("Parameters img_dem, img_snow, img_cloud and outhist are required")

def compute_nb_pixels(img, lower, upper, ram=None):
    """ Create and configure the ComputeNbPixels application
        using otb.Registry.CreateApplication("ComputeNbPixels")

    Keyword arguments:
    TODO
    """
    if img:
        logging.info("Processing ComputeNbPixels with args:")
        logging.info(img)
        logging.info(lower)
        logging.info(upper)

        computeNbPixelsApp = otb.Registry.CreateApplication("ComputeNbPixels")
        computeNbPixelsApp.SetParameterString("in", img)

        # Scalar parameter
        computeNbPixelsApp.SetParameterInt("lower", lower)
        computeNbPixelsApp.SetParameterInt("upper", upper)

        if ram is not None:
            logging.info("ram = " + str(ram))
            computeNbPixelsApp.SetParameterString("ram", str(ram))

        return computeNbPixelsApp
    else:
        logging.error("Parameters img is required")

def super_impose(img_in, mask_in, img_out, interpolator=None,
                 fill_value=None, ram=None, out_type=None):
    """ Create and configure the otbSuperImpose application
        using otb.Registry.CreateApplication("Superimpose")

    Keyword arguments:
    img_in -- the reference image in
    mask_in -- the input mask to superimpose on img_in
    img_out -- the output image
    fill_value -- the fill value for area outside the reprojected image
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if img_in and mask_in and img_out:
        logging.info("Processing otbSuperImpose with args:")
        logging.info("img_in = " + img_in)
        logging.info("mask_in = " + mask_in)
        logging.info("img_out = " + img_out)
        logging.info("interpolator = " + interpolator)

        super_impose_app = otb.Registry.CreateApplication("Superimpose")
        super_impose_app.SetParameterString("inr", img_in)
        super_impose_app.SetParameterString("inm", mask_in)
        super_impose_app.SetParameterString("out", img_out)
        super_impose_app.SetParameterString("interpolator", interpolator)

        if fill_value is not None:
            logging.info("fill_value = " + str(fill_value))
            super_impose_app.SetParameterFloat("fv", fill_value)
        if ram is not None:
            logging.info("ram = " + str(ram))
            super_impose_app.SetParameterString("ram", str(ram))
        if out_type is not None:
            logging.info("out_type = " + str(out_type))
            super_impose_app.SetParameterOutputImagePixelType("out", out_type)
        return super_impose_app
    else:
        logging.error("Parameters img_in, img_out and mask_in are required")

def compute_contour(img_in, img_out, foreground_value, fullyconnected, \
                    ram=None, out_type=None):
    """ Create and configure the Compute Contours application
        using otb.Registry.CreateApplication("ComputeContours")

    Keyword arguments:
    img_in -- the input image
    img_out -- the output image
    foreground_value -- the value corresponding to the region to extract
    fullyconnected -- boolean to use 8 connexity
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if img_in and foreground_value:
        logging.info("Processing ComputeContours with args:")
        logging.info("in = " + img_in)
        logging.info("foreground_value = " + foreground_value)
        logging.info("fullyconnected = " + str(fullyconnected))

        cloudMaskApp = otb.Registry.CreateApplication("ComputeContours")
        cloudMaskApp.SetParameterString("foregroundvalue", foreground_value)
        if img_out is not None:
            logging.info("out = " + img_out)
            cloudMaskApp.SetParameterString("out", img_out)
        if fullyconnected:
            cloudMaskApp.SetParameterInt("fullyconnected", 1)
            cloudMaskApp.SetParameterString("inputmask", img_in)
        else:
            cloudMaskApp.SetParameterInt("fullyconnected", 0)
        if ram is not None:
            logging.info("ram = " + str(ram))
            cloudMaskApp.SetParameterString("ram", str(ram))
        if out_type is not None:
            logging.info("outtype = " + str(out_type))
            cloudMaskApp.SetParameterOutputImagePixelType("out", out_type)
        return cloudMaskApp
    else:
        logging.error("Parameters img_in and foreground_value are required")


def confusion_matrix(img_in, ref_in, out, ref_no_data=None, ram=None):
    """ Create and configure the otbComputeConfusionMatrix application
        using otb.Registry.CreateApplication("ComputeConfusionMatrix")

    Keyword arguments:
    img_in -- the image in
    out -- the matrix output
    ref_in -- the reference image in
    ref_no_data -- the nodata value for  pixels in ref raster
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if img_in and ref_in and out:
        logging.info("Processing otbComputeConfusionMatrix with args:")
        logging.info("img_in = " + img_in)
        logging.info("out = " + out)
        logging.info("ref_in = " + ref_in)

        super_impose_app = otb.Registry.CreateApplication("ComputeConfusionMatrix")
        super_impose_app.SetParameterString("in", img_in)
        super_impose_app.SetParameterString("ref", "raster")
        super_impose_app.SetParameterString("ref.raster.in", ref_in)
        super_impose_app.SetParameterString("out", out)

        if ref_no_data is not None:
            logging.info("ref_no_data = " + str(ref_no_data))
            super_impose_app.SetParameterInt("ref.raster.nodata", ref_no_data)
        if ram is not None:
            logging.info("ram = " + str(ram))
            super_impose_app.SetParameterString("ram", str(ram))
        return super_impose_app
    else:
        logging.error("Parameters img_in, out and ref_in are required")

def get_app_output(app, out_key, mode="RUNTIME"):
    """ Custom function to return the output of an OTB application
        depending on the mode, the function return either:
        - to an object correcponding to the output in memory
        - or a filename corresponding to the output written on the disk
    """
    app_output = app.GetParameterString(out_key)
    if "?" in app_output:
        app_output = app_output.split("?")[0]

    if mode == "RUNTIME":
        app.Execute()
        app_output = app.GetParameterOutputImage(out_key)
    elif mode == "DEBUG":
        app.ExecuteAndWriteOutput()
        # @TODO uneffective command, this must be done outside the function
        app = None
    else:
        logging.error("Unexpected mode")
    return app_output
