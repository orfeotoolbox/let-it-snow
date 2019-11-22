#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import subprocess
import logging
import ast

from osgeo import gdal, gdalconst, osr

def show_help():
    print("This script is used to compute srtm mask from a vrt file to a region extent")
    print("Usage: preprocessing.py srtm.vrt img.tif output.tif")


def get_extent(geotransform, cols, rows):
    extent = []
    xarr = [0, cols]
    yarr = [0, rows]

    for px in xarr:
        for py in yarr:
            x = geotransform[0] + (px * geotransform[1]) + \
                (py * geotransform[2])
            y = geotransform[3] + (px * geotransform[4]) + \
                (py * geotransform[5])
            extent.append([x, y])
        yarr.reverse()
    return extent


def build_dem(psrtm, pimg, pout, ram, nbThreads):
    # load datasets
    source_dataset = gdal.Open(psrtm, gdalconst.GA_Update)
    source_geotransform = source_dataset.GetGeoTransform()
    source_projection = source_dataset.GetProjection()

    target_dataset = gdal.Open(pimg, gdalconst.GA_Update)
    target_geotransform = target_dataset.GetGeoTransform()
    target_projection = target_dataset.GetProjection()
    wide = target_dataset.RasterXSize
    high = target_dataset.RasterYSize

    # compute extent xminymin and yminymax
    extent = get_extent(target_geotransform, wide, high)
    logging.info("Extent: " + str(extent))
    te = "".join(str(extent[1] + extent[3]))  # xminymin xmaxymax
    te = ast.literal_eval(te)
    # Not use when moving gdalwarp to subprocess call
    # te = ' '.join([str(x) for x in te])
    logging.info(te)


    # get target resolution
    resolution = target_geotransform[1]  # or geotransform[5]
    logging.info(str(resolution))

    # get target projection
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromWkt(target_projection)
    spatial_ref_projection = spatial_ref.ExportToProj4()
    logging.info(spatial_ref_projection)

    # TODO Use GDAL Python API instead
    # gdalwarp call
    # TODO use RAM and thread options from gdal here (from json parameters)
    # FIXME: srcnodata is hard coded to -32768 only valid for SRTM
    try:
        p=subprocess.check_output(
        ["gdalwarp",
         "-overwrite",
         "-srcnodata",
         str(-32768),
         "-dstnodata",
         str(0),
         "-wm",
         str(ram),
         #"-wo NUM_THREADS="+str(nbThreads),
         "-tr",
         str(resolution),
         str(resolution),
         "-r",
         "cubicspline",
         "-te",
         str(te[0]),
         str(te[1]),
         str(te[2]),
         str(te[3]),
         "-t_srs",
         str(spatial_ref_projection),
         str(psrtm),
         str(pout)
        ]
         )

    except subprocess.CalledProcessError as e:
        print e.output
        print 'Error running command: ' + str(e.cmd) + ' see above shell error'
        print 'Return code: ' + str(e.returncode)
        return e.returncode
    
def main(argv):
        # parse files path
    psrtm = argv[1]
    pimg = argv[2]
    pout = argv[3]
    ram = 128
    nbThreads = 1
    build_dem(psrtm, pimg, pout, ram, nbThreads)


if __name__ == "__main__":
    # Set logging level and format.
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s')
    
    if len(sys.argv) != 4:
        show_help()
    else:
        main(sys.argv)
