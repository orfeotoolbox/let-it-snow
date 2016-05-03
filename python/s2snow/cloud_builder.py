import sys, os, numpy, random
import os.path as op

import gdal, gdalconst
from subprocess import call

def show_help():
	print "This script is used to create clouds on data"
	print "Usage: cloud_builder.py mode plaincloudthreshold randomcloudthreshold inputpath outputplaincloudpath ouputrandomcloudpath"
        print "Mode : 0 %plain cloud image, 1 %random cloud image, 2 both"
def main(argv):
    mode = argv[1]
    mode = int(mode)
    plain_cloud_threshold = argv[2]
    plain_cloud_threshold = float(plain_cloud_threshold) / 100
    random_cloud_threshold = argv[3]
    input_path = argv[4]
    output_plain_cloud_path = argv[5]
    output_random_cloud_path = argv[6]
    
    dataset = gdal.Open(input_path, gdalconst.GA_ReadOnly)
    wide = dataset.RasterXSize
    high = dataset.RasterYSize
    
    if(mode == 0 or mode == 2):
        #build half cloud image
        str_exp = "idxX>"+str(int(wide*plain_cloud_threshold))+"?im1b1:205"
        call(["otbcli_BandMathX", "-il", input_path, "-out", output_plain_cloud_path, "-exp", str_exp])
    if(mode == 1 or mode == 2):
        #build random cloud image
        band = dataset.GetRasterBand(1)
        array = band.ReadAsArray(0, 0, wide, high)
        for i in range(0, wide):
            for j in range(0, high):
                if(random.randint(0, 100) < random_cloud_threshold):
                    array[i,j] = 205
                    
        output_random_cloud_raster = gdal.GetDriverByName('GTiff').Create(output_random_cloud_path, wide, high, 1 ,gdal.GDT_Byte)
        output_random_cloud_raster.GetRasterBand(1).WriteArray(array) 
        output_random_cloud_raster.FlushCache()

        # georeference the image and set the projection
        output_random_cloud_raster.SetGeoTransform(dataset.GetGeoTransform())
        output_random_cloud_raster.SetProjection(dataset.GetProjection()) 
    
if __name__ == "__main__":
    if len(sys.argv) != 7:
        show_help()
    else:
        main(sys.argv)

