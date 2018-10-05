#!/bin/bash
#PBS -N TheiaNeige
#PBS -j oe
#PBS -l select=1:ncpus=8:mem=20000mb
#PBS -l walltime=24:00:00
# run LIS for one Sentinel-2 Level-2A tile and one date (walltime is higher)
# specify the path to the tile folder, the path the DEM and the template configuration file (.json)
# First argument is the tile name (nnccc): qsub -v config="path/to/config/json" run_snow_annual_map.sh


if [ -z $config ]; then
  echo "config is not set, exit"
  exit
fi

echo $config

#config_list=`ls /work/OT/siaa/Theia/Neige/Snow_Annual_Maps/*/*.json`

#Load LIS modules
#module load lis/develop
source /home/qt/salguesg/load_lis.sh

#configure gdal_cachemax to speedup gdal polygonize and gdal rasterize (half of requested RAM)
export GDAL_CACHEMAX=2048
echo $GDAL_CACHEMAX
export PATH=/home/qt/salguesg/local/bin:/home/qt/salguesg/local/bin:$PATH
echo $PATH

# run the snow detection
date ; echo "START run_snow_annual_map.py $config"
run_snow_annual_map.py $config
date ; echo "END run_snow_annual_map.py"
