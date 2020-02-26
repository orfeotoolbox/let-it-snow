#!/usr/bin/env python3
# This script computes the Permanent snow area AKA "PSL" in CoSIMS from annnual snow map outputs
# The PSL of a given year is defined as pixels where snow was always observed when possible from May 01 to Sep 01 of this year
# In HAL the dependencies are loaded with module load lis/develop
# Author: Simon Gascoin

import rasterio
import numpy as np
import os,sys
import numpy as np

# input file is input_dates.txt
# Example: f="/work/OT/siaa/Theia/Neige/SNOW_ANNUAL_MAP_LIS_1.5/S2_with_L8_Densification//T32TNS_20170901_20180831/tmpdir/multitemp_cloud_mask.vrt"

f=sys.argv[1]

fdir=os.path.split(os.path.split(f)[0])[0]
fdates=fdir+os.sep+"input_dates.txt"
d=np.loadtxt(fdates)
# Creates May 01 for the year
May01=np.round(d[-1]/10000)*10000+501
# find index of closest date
idx = (np.abs(d - May01)).argmin()

srcObs=rasterio.open(f, 'r')
srcSnow=rasterio.open(os.path.split(f)[0]+os.sep+"multitemp_snow_mask.vrt", 'r')
n=srcObs.meta["count"]
# read only from the date which is the closest to May 01 up to Sep 01
snow = srcSnow.read(range(idx,n))
obs = srcObs.read(range(idx,n))
# pixels in p are either snow (1), cloud (1) or no snow (0)
p=snow+obs
# PSL corresponds to pixels always flagged as snow or cloud
PSL=np.all(p,axis=0)

# output file suffix
outfile=os.path.split(fdir)[1]

# export PSL...tif in the parent folder of the input file
with rasterio.Env():
    profile = srcObs.profile
    profile.update(
        dtype=rasterio.uint8,
        driver='GTiff',
        count=1)

    with rasterio.open("{}/PSL_{}.tif".format(fdir,outfile), 'w', **profile) as dst:
        dst.write(PSL.astype(rasterio.uint8), 1)
