import sys, numpy
from scipy import ndimage
from subprocess import call
import os
import os.path as op
import gdal
import gdalconst

def show_help():
	print "This script is used to remove clouds from snow data"
	print "Usage: TODO"
        print "TODO"
def main(argv):
    m2_path = argv[1]
    m1_path = argv[2]
    t0_path = argv[3]
    p1_path = argv[4]
    p2_path = argv[5]
    dem_path = argv[6]
    metadata_path = argv[7]
    output_path = argv[8]
    
    #S(y,x,t) = 1 if (S(y,x,t-1) = 1 and S(y,x,t+1) = 1) 
    call(["otbcli_BandMath", "-il", m1_path, t0_path, p1_path, "-out", op.join(output_path, "cloud_removal_pass1.tif"), "-exp", "im2b1==100?100:(im1b1==100&&im3b1==100)?100:im2b1"])
    #S(y,x,t) = 1 if (S(y,x,t-2) = 1 and S(y,x,t+1) = 1)
    call(["otbcli_BandMath", "-il", m2_path, op.join(output_path, "cloud_removal_pass1.tif"), p1_path, "-out", op.join(output_path, "cloud_removal_pass2.tif"), "-exp", "im2b1==100?100:(im1b1==100&&im3b1==100)?100:im2b1"])
     #S(y,x,t) = 1 if (S(y,x,t-1) = 1 and S(y,x,t+2) = 1)
    call(["otbcli_BandMath", "-il", m1_path, op.join(output_path, "cloud_removal_pass2.tif"), p2_path, "-out", op.join(output_path, "cloud_removal_pass3.tif"), "-exp", "im2b1==100?100:(im1b1==100&&im3b1==100)?100:im2b1"])
    
    #S(y,x,t) = 1 if (H(x,y) < Hsmin(t))
    #TODO retreive ZS test if - 70% de nuages
    ZS_min=2800
    print ZS_min
    call(["otbcli_BandMath", "-il", op.join(output_path, "cloud_removal_pass3.tif"), dem_path, "-out", op.join(output_path, "cloud_removal_pass4.tif"), "-exp", "im1b1==205?(im2b1<"+str(ZS_min)+"?255:im1b1):im1b1"])
 
    #S(y,x,t) = 1 if (H(x,y) > Hsmax(t))
    ZS_max = -1
    print ZS_max
    if(ZS_max != -1):
            call(["otbcli_BandMath", "-il", op.join(output_path, "cloud_removal_pass4.tif"), dem_path, "-out", op.join(output_path, "cloud_removal_pass5.tif"), "-exp", "im1b1==205?(im2b1>"+str(ZS_max)+"?255:im1b1):im1b1"])
    #Do nothing but create image still
    else:
            call(["otbcli_BandMath", "-il", op.join(output_path, "cloud_removal_pass4.tif"), dem_path, "-out", op.join(output_path, "cloud_removal_pass5.tif"), "-exp", "im1b1"])
        
    # four-pixels neighboring
    dataset_pass5 = gdal.Open(op.join(output_path, "cloud_removal_pass5.tif"), gdalconst.GA_ReadOnly)
    wide = dataset_pass5.RasterXSize
    high = dataset_pass5.RasterYSize
    band_pass5 = dataset_pass5.GetRasterBand(1)
    array_pass5 = band_pass5.ReadAsArray(0, 0, wide, high)
    
    # Get west, north, east & south elements for [1:-1,1:-1] region of input array
    W = array_pass5[1:-1,:-2]
    N  = array_pass5[:-2,1:-1]
    E = array_pass5[1:-1,2:]
    S  = array_pass5[2:,1:-1]

    # Check if all four arrays have 100 for that same element in that region
    mask = (W == 100) & (N == 100) & (E == 100) & (S == 100) & (array_pass5[1:-1,1:-1] == 205)
    
    # Use the mask to set corresponding elements in a copy version as 100
    array_pass6 = array_pass5.copy()
    array_pass6[1:-1,1:-1][mask] = 100
    
    #create file
    output_pass6 = gdal.GetDriverByName('GTiff').Create(op.join(output_path, "cloud_removal_pass6.tif"), wide, high, 1 ,gdal.GDT_Byte)
    output_pass6.GetRasterBand(1).WriteArray(array_pass6)
    
    # georeference the image and set the projection
    output_pass6.SetGeoTransform(dataset_pass5.GetGeoTransform())
    output_pass6.SetProjection(dataset_pass5.GetProjection()) 
    output_pass6 = None
    
    # S(y,x,t) = 1 if (S(y+k,x+k,t)(kc(-1,1)) = 1 and H(y+k,x+k)(kc(-1,1)) < H(y,x))
    dataset_pass6 = gdal.Open(op.join(output_path, "cloud_removal_pass6.tif"), gdalconst.GA_ReadOnly)    
    wide = dataset_pass6.RasterXSize
    high = dataset_pass6.RasterYSize
    band_pass6 = dataset_pass6.GetRasterBand(1)
    array_pass6 = band_pass6.ReadAsArray(0, 0, wide, high)
    
    dataset_dem = gdal.Open(op.join(output_path, "srtm.tif"), gdalconst.GA_ReadOnly)
    band_dem = dataset_dem.GetRasterBand(1)
    array_dem = band_dem.ReadAsArray(0, 0, wide, high)
    
    # Get 8 neighboring pixels for raster and dem 
    W = array_pass6[1:-1,:-2]
    NW = array_pass6[:-2,:-2]
    N  = array_pass6[:-2,1:-1]
    NE = array_pass6[:-2,2:]
    E = array_pass6[1:-1,2:]
    SE = array_pass6[2:,2:]
    S  = array_pass6[2:,1:-1]
    SW = array_pass6[2:,:-2]
    
    Wdem = array_dem[1:-1,:-2]
    NWdem = array_dem[:-2,:-2]
    Ndem  = array_dem[:-2,1:-1]
    NEdem = array_dem[:-2,2:]
    Edem = array_dem[1:-1,2:]
    SEdem = array_dem[2:,2:]
    Sdem  = array_dem[2:,1:-1]
    SWdem = array_dem[2:,:-2]

    
    mask1 =((((W == 100) & (array_dem[1:-1,1:-1] > Wdem)) | ((N == 100) & (array_dem[1:-1,1:-1] > Ndem)) | ((E == 100) & (array_dem[1:-1,1:-1] > Edem)) | ((S == 100) & (array_dem[1:-1,1:-1] > Sdem))  | ((NW == 100) & (array_dem[1:-1,1:-1] > NWdem)) | ((NE == 100) & (array_dem[1:-1,1:-1] > NEdem)) | ((SE == 100) & (array_dem[1:-1,1:-1] > SEdem)) | ((SW == 100) & (array_dem[1:-1,1:-1] > SWdem))) & (array_pass5[1:-1,1:-1] == 205))
    
    # Use the mask to set corresponding elements in a copy version as 100
    array_pass7 = array_pass6.copy()
    array_pass7[1:-1,1:-1][mask] = 100

    #create file
    output_pass7 = gdal.GetDriverByName('GTiff').Create(op.join(output_path, "cloud_removal_pass7.tif"), wide, high, 1 ,gdal.GDT_Byte)
    output_pass7.GetRasterBand(1).WriteArray(array_pass7) 
        
    # georeference the image and set the projection
    output_pass7.SetGeoTransform(dataset_pass6.GetGeoTransform())
    output_pass7.SetProjection(dataset_pass6.GetProjection()) 
    output_pass7 = None

if __name__ == "__main__":
    if len(sys.argv) != 9:
        show_help()
    else:
        main(sys.argv)

