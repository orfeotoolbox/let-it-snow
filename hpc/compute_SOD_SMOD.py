import rasterio
import numpy as np
import itertools,operator,sys,os

# input file is the interpolated daily raster (1=snow,0=nosnow)
# Example: /work/OT/siaa/Theia/Neige/SNOW_ANNUAL_MAP_LIS_1.5/S2_with_L8_Densification//T31TCH_20160901_20170831/DAILY_SNOW_MASKS_T31TCH_20160901_20170831.tif             
f=sys.argv[1]
src=rasterio.open(f, 'r')
print "Start compute_SOD_SMOD.py using: ",f

# memory heavy, load all raster bands in memory 
# runs in 23 min in HAl with 100 Gb RAM: qsub -I -l select=1:ncpus=4:mem=100000mb -l walltime=05:00:00
# 20 Gb should be fine: qsub -I -l walltime=00:50:00 -l select=1:ncpus=1:mem=20000mb
W = src.read(range(1,365))

n=np.shape(W)[1]
m=np.shape(W)[2]
SOD=np.zeros((n,m),dtype='uint16')
SMOD=np.zeros((n,m),dtype='uint16')
for i in np.arange(0,n):
     for j in np.arange(0,m):
         w = W[:,i,j]
         if np.sum(w)>10:
             # one-liner from https://stackoverflow.com/questions/40166522/find-longest-sequence-of-0s-in-the-integer-list
             r = max((list(y) for (x,y) in itertools.groupby((enumerate(w)),operator.itemgetter(1)) if x == 1), key=len)
             SMOD[i,j]=r[-1][0]
             SOD[i,j]=r[0][0]

# export in the same folder as the input file
with rasterio.Env():
    profile = src.profile
    profile.update(
        dtype=rasterio.uint16,
        count=1)

    with rasterio.open("{}/SMOD_{}".format(os.path.split(f)[0],os.path.split(f)[1]), 'w', **profile) as dst:
        dst.write(SMOD.astype(rasterio.uint16), 1)
        
    with rasterio.open("{}/SOD_{}".format(os.path.split(f)[0],os.path.split(f)[1]), 'w', **profile) as dst:
        dst.write(SOD.astype(rasterio.uint16), 1)

print "End of compute_SOD_SMOD.py"

