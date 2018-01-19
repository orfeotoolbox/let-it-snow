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
            if isinstance(image, basestring):
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

def compute_snow_mask(pass1, pass2, cloud_pass1, cloud_refine, out, \
                      ram=None, out_type=None):
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
        logging.error("Parameters pass1, pass2, cloud_pass1, \
                       cloud_refine and out are required")

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
            if isinstance(image, basestring):
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
            cloudMaskApp.SetParameterString("fullyconnected", "true")
        cloudMaskApp.SetParameterString("inputmask", img_in)
        if ram is not None:
            logging.info("ram = " + str(ram))
            cloudMaskApp.SetParameterString("ram", str(ram))
        if out_type is not None:
            logging.info("outtype = " + str(out_type))
            cloudMaskApp.SetParameterOutputImagePixelType("out", out_type)
        return cloudMaskApp
    else:
        logging.error("Parameters img_in and foreground_value are required")

def super_impose(img_in, mask_in, img_out, interpolator = None,
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
    app_output = app.GetParameterString(out_key)

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
