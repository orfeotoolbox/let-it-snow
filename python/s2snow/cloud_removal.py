import sys, numpy, json, multiprocessing
from scipy import ndimage
from subprocess import call
import os
import os.path as op
import gdal
import gdalconst

def show_help():
	print "This script is used to remove clouds from snow data"
	print "Usage: cloud_removal.py config.json"

def step1(m1_path, t0_path, p1_path, output_path, ram):
    #S(y,x,t) = 1 if (S(y,x,t-1) = 1 and S(y,x,t+1) = 1) 
    call(["otbcli_BandMath","-ram", str(ram), "-il", m1_path, t0_path, p1_path, "-out", output_path, "-exp", "im2b1==100?100:(im1b1==100&&im3b1==100)?100:im2b1"])

def step2(m2_path, m1_path, t0_path, p1_path, p2_path, output_path, ram):
    #S(y,x,t) = 1 if (S(y,x,t-2) = 1 and S(y,x,t+1) = 1)
	call(["otbcli_BandMath","-ram", str(ram), "-il", m2_path, t0_path, p1_path, "-out", output_path, "-exp", "im2b1==100?100:(im1b1==100&&im3b1==100)?100:im2b1"])
    #S(y,x,t) = 1 if (S(y,x,t-1) = 1 and S(y,x,t+2) = 1)
	call(["otbcli_BandMath","-ram", str(ram), "-il", m1_path, output_path, p2_path, "-out", output_path, "-exp", "im2b1==100?100:(im1b1==100&&im3b1==100)?100:im2b1"])

def step3(t0_path, dem_path, hs_min, hs_max, output_path, ram):
    #S(y,x,t) = 1 if (H(x,y) < Hsmin(t))
    call(["otbcli_BandMath","-ram", str(ram), "-il", t0_path, dem_path, "-out", output_path, "-exp", "im1b1==205?(im2b1<"+str(hs_min)+"?255:im1b1):im1b1"])
 
    #S(y,x,t) = 1 if (H(x,y) > Hsmax(t))
    call(["otbcli_BandMath","-ram", str(ram), "-il", output_path, dem_path, "-out", output_path, "-exp", "im1b1==205?(im2b1>"+str(hs_max)+"?255:im1b1):im1b1"])

def step4(t0_path, output_path, window_size):
    
	# four-pixels neighboring    
	print "Starting step 4"
	dataset = gdal.Open(t0_path, gdalconst.GA_ReadOnly)
	wide = dataset.RasterXSize
	high = dataset.RasterYSize
	band = dataset.GetRasterBand(1)
	array = band.ReadAsArray(0, 0, wide, high)

	# Get west, north, east & south elements for [1:-1,1:-1] region of input array
	W = array[1:-1,:-2]
	N  = array[:-2,1:-1]
	E = array[1:-1,2:]
	S  = array[2:,1:-1]
	
	# Check if all four arrays have 100 for that same element in that region
	mask = (W == 100) & (N == 100) & (E == 100) & (S == 100) & (array[1:-1,1:-1] == 205)
	
	# Use the mask to set corresponding elements in a copy version as 100
	array_out = array.copy()
	array_out[1:-1,1:-1][mask] = 100
	
	#create file
	output = gdal.GetDriverByName('GTiff').Create(output_path, wide, high, 1 ,gdal.GDT_Byte)
	output.GetRasterBand(1).WriteArray(array_out)
	
	# georeference the image and set the projection
	output.SetGeoTransform(dataset.GetGeoTransform())
	output.SetProjection(dataset.GetProjection()) 
	output = None
	print "End of step 4"

def step5(t0_path, dem_path, output_path, window_size):
	# S(y,x,t) = 1 if (S(y+k,x+k,t)(kc(-1,1)) = 1 and H(y+k,x+k)(kc(-1,1)) < H(y,x))
	print "Starting step 5"
	dataset = gdal.Open(t0_path, gdalconst.GA_ReadOnly)    
	wide = dataset.RasterXSize
	high = dataset.RasterYSize
	band = dataset.GetRasterBand(1)
	array = band.ReadAsArray(0, 0, wide, high)

	dataset_dem = gdal.Open(dem_path, gdalconst.GA_ReadOnly)
	band_dem = dataset_dem.GetRasterBand(1)
	array_dem = band_dem.ReadAsArray(0, 0, wide, high)
	
	# Get 8 neighboring pixels for raster and dem 
	W = array[1:-1,:-2]
	NW = array[:-2,:-2]
	N  = array[:-2,1:-1]
	NE = array[:-2,2:]
	E = array[1:-1,2:]
	SE = array[2:,2:]
	S  = array[2:,1:-1]
	SW = array[2:,:-2]
	
	Wdem = array_dem[1:-1,:-2]
	NWdem = array_dem[:-2,:-2]
	Ndem  = array_dem[:-2,1:-1]
	NEdem = array_dem[:-2,2:]
	Edem = array_dem[1:-1,2:]
	SEdem = array_dem[2:,2:]
	Sdem  = array_dem[2:,1:-1]
	SWdem = array_dem[2:,:-2]

	arrdem = array_dem[1:-1,1:-1]
	mask =((((W == 100) & (arrdem > Wdem)) | ((N == 100) & (arrdem > Ndem)) | ((E == 100) & (arrdem > Edem)) | ((S == 100) & (arrdem > Sdem))  | ((NW == 100) & (arrdem > NWdem)) | ((NE == 100) & (arrdem > NEdem)) | ((SE == 100) & (arrdem > SEdem)) | ((SW == 100) & (arrdem > SWdem))) & (array[1:-1,1:-1] == 205))

	# Use the mask to set corresponding elements in a copy version as 100
	array_out = array.copy()
	array_out[1:-1,1:-1][mask] = 100
	
	#create file
	output = gdal.GetDriverByName('GTiff').Create(output_path, wide, high, 1 ,gdal.GDT_Byte)
	output.GetRasterBand(1).WriteArray(array) 
	
	# georeference the image and set the projection
	output.SetGeoTransform(dataset.GetGeoTransform())
	output.SetProjection(dataset.GetProjection()) 
	output = None
	print "End of step 5"

def main(argv):

	json_file=argv[1]
	with open(json_file) as json_data_file:
		data = json.load(json_data_file)
		
	general=data["general"]
	output_path=general.get("pout")
	ram=general.get("ram", 512)

	try:
		nb_defaultThreads = multiprocessing.cpu_count()
	except NotImplementedError:
		print "Cannot get max number of CPU on the system. nbDefaultThreads set to 1."  
		nb_defaultThreads = 1
		
	nb_threads=general.get("nb_threads", nb_defaultThreads)
	os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"]=str(nb_threads)
	
	inputs=data["inputs"]    
	m2_path=inputs.get("m2Path")
	m1_path=inputs.get("m1Path")
	t0_path=inputs.get("t0Path")
	p1_path=inputs.get("p1Path")
	p2_path=inputs.get("p2Path")
	dem_path=inputs.get("demPath")

	parameters=data["parameters"]
	hs_min=parameters.get("hsMin")
	hs_max=parameters.get("hsMax")
	window_size=parameters.get("windowSize")
	
	steps=data["steps"]
	s1=steps.get("s1", True)
	s2=steps.get("s2", True)
	s3=steps.get("s3", True)
	s4=steps.get("s4", True)
	s5=steps.get("s5", True)
	
	latest_file_path=t0_path
	if s1:
		temp_output_path=op.join(output_path, "cloud_removal_output_step1.tif")
		step1(m1_path, latest_file_path, p1_path, temp_output_path, ram)
		latest_file_path=temp_output_path
	if s2:
		temp_output_path=op.join(output_path, "cloud_removal_output_step2.tif")
		step2(m2_path, m1_path, latest_file_path, p1_path, p2_path, temp_output_path, ram)
		latest_file_path=temp_output_path
	if s3:
		temp_output_path=op.join(output_path, "cloud_removal_output_step3.tif")
		step3(latest_file_path, dem_path, hs_min, hs_max, temp_output_path, ram)
		latest_file_path=temp_output_path
	if s4:
		temp_output_path=op.join(output_path, "cloud_removal_output_step4.tif")
		step4(latest_file_path, temp_output_path, window_size)
		latest_file_path=temp_output_path
	if s5:
		output_path=op.join(output_path, "cloud_removal_output_step5.tif")
		step5(latest_file_path, dem_path, output_path, window_size)
		latest_file_path=temp_output_path

if __name__ == "__main__":
    if len(sys.argv) != 2:
        show_help()
    else:
        main(sys.argv)

