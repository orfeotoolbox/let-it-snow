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
        if img_out is not None:
            logging.info("out = " + img_out)
            cloudMaskApp.SetParameterString("out", img_out)
        logging.info("foreground_value = " + foreground_value)
        logging.info("fullyconnected = " + str(fullyconnected))

        cloudMaskApp = otb.Registry.CreateApplication("ComputeContours")
        cloudMaskApp.SetParameterString("foregroundvalue", foreground_value)
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
