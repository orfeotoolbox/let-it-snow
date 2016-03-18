import sys, os, numpy, random
import os.path as op

import gdal, gdalconst
from subprocess import call

def main(argv):
    inputpath = "/home/grizonnetm/Data-Neige/output_lis_landsat/N2A_France-MetropoleD0005H0001/LANDSAT8_OLITIRS_XS_20140410_N2A_France-MetropoleD0005H0001"
    outputpath ="/home/klempkat/let-it-snow/cloud_removal/data"
    final_mask = op.join(inputpath, "final_mask.tif")
    dataset = gdal.Open(final_mask, gdalconst.GA_ReadOnly)
    wide = dataset.RasterXSize
    high = dataset.RasterYSize
    
    #build half cloud image
    call(["otbcli_BandMathX", "-il", final_mask, "-out", op.join(outputpath,"final_mask_half.tif")])
    
    #build random cloud image
    band = dataset.GetRasterBand(1)
    array = band.ReadAsArray(0, 0, wide, high)
    cloud_threshold = 25
    for i in range(0, wide):
        for j in range(0, high):
            if(random.randint(0, 100) < cloud_threshold):
                array[i,j] = 205
    
    output_random_cloud_raster = gdal.GetDriverByName('GTiff').Create(op.join(outputpath,"final_mask_random.tif"), wide, high, 1 ,gdal.GDT_Byte)
    output_random_cloud_raster.GetRasterBand(1).WriteArray(array) 
    output_random_cloud_raster.FlushCache()

    # georeference the image and set the projection
    output_random_cloud_raster.SetGeoTransform(dataset.GetGeoTransform())
    output_random_cloud_raster.SetProjection(dataset.GetProjection()) 
    
if __name__ == "__main__":
    main(sys.argv)
