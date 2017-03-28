#!/usr/bin/env python

from osgeo import gdal, gdalconst, osr
import sys
import subprocess
import ast


def show_help():
    print "This script is used to compute srtm mask from a vrt file to a region extent"
    print "Usage: preprocessing.py srtm.vrt img.tif output.tif"


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


def build_dem(psrtm, pimg, pout):
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
    print("Extent: " + str(extent))
    te = "".join(str(extent[1] + extent[3]))  # xminymin xmaxymax
    te = ast.literal_eval(te)
    te = ' '.join([str(x) for x in te])
    print(te)

    # get target resolution
    resolution = target_geotransform[1]  # or geotransform[5]
    print(str(resolution))

    # get target projection
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromWkt(target_projection)
    spatial_ref_projection = spatial_ref.ExportToProj4()
    print(spatial_ref_projection)

    # gdalwarp call
    subprocess.check_output(
        "gdalwarp -dstnodata -32768 -tr " +
        str(resolution) +
        " " +
        str(resolution) +
        " -r cubicspline -te " +
        te +
        " -t_srs '" +
        spatial_ref_projection +
        "' " +
        psrtm +
        " " +
        pout,
        stderr=subprocess.STDOUT,
        shell=True)


def main(argv):
        # parse files path
    psrtm = argv[1]
    pimg = argv[2]
    pout = argv[3]
    build_dem(psrtm, pimg, pout)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        show_help()
    else:
        main(sys.argv)
