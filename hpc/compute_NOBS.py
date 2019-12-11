#!/usr/bin/env python
# This script computes NOBS.tif, the number of clear observations to compute the SCD, SMOD and SOD syntheses
# In HAL the dependencies are loaded with module load lis/develop
# Author: Simon Gascoin

import rasterio
import numpy as np
import os,sys

# input file is the cloud mask vrt
# Example: /work/OT/siaa/Theia/Neige/SNOW_ANNUAL_MAP_LIS_1.5/S2_with_L8_Densification//T32TLP_20180901_20190831/tmpdir/multitemp_cloud_mask.vrt
f=sys.argv[1]
src=rasterio.open(f, 'r')
n=src.meta["count"]
W = src.read(range(1,n))
S=n-np.sum(W,axis=0)

outdir=os.path.split(os.path.split(f)[0])[0]
outfile=os.path.split(outdir)[1]


# export NOBS.tif in the parent folder of the input file
with rasterio.Env():
    profile = src.profile
    profile.update(
        dtype=rasterio.uint16,
        driver='GTiff',
        count=1)

    with rasterio.open("{}/NOBS_{}.tif".format(outdir,outfile), 'w', **profile) as dst:
        dst.write(S.astype(rasterio.uint16), 1)


