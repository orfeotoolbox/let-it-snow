#!/bin/bash
#PBS -N TheiaNeigeRunSnowAnnualMap
#PBS -j oe
#PBS -l select=1:ncpus=8:mem=20000mb
#PBS -l walltime=04:20:00
# run LIS for one Sentinel-2 Level-2A tile and one date (walltime is higher)
# specify the path to the tile folder, the path the DEM and the template configuration file (.json)
# First argument is the tile name (nnccc): qsub -v config="path/to/config/json",overwrite="false"  run_snow_annual_map.sh


if [ -z $config ]; then
  echo "config is not set, exit"
  exit
fi

echo $config

if [ -z $overwrite ]; then
  echo "overwrite is not set, not overwrite will be done"
  overwrite="false"
fi

expected_target_path=$(dirname $config)
echo "Expected output path $expected_target_path"
echo $(ls -A -- ${expected_target_path}/*.tif)
if [ -n "$(ls -A -- ${expected_target_path}/*.tif)" ]; then
    echo "$expected_target_path already contains tif results!"
    if [ $overwrite == "false" ]; then
        echo "exiting to avoid overwrite"
        exit 1
    fi
fi

outpath=$(dirname $config)

#Load LIS modules
module load lis/1.5

#configure gdal_cachemax to speedup gdal polygonize and gdal rasterize (half of requested RAM)
export GDAL_CACHEMAX=2048
echo $GDAL_CACHEMAX

# run the snow detection
date ; echo "START run_snow_annual_map.py $config"
run_snow_annual_map.py $config
date ; echo "END run_snow_annual_map.py"

chgrp -R lis_admin $expected_target_path
chmod 775 -R $expected_target_path
echo "Results available under $expected_target_path"
