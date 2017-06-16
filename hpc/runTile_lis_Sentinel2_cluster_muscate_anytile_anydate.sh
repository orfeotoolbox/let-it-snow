#!/bin/bash
#PBS -N TheiaNeige
#PBS -j oe
#PBS -l select=1:ncpus=1:mem=4000mb
#PBS -l walltime=00:55:00
# run LIS for one Sentinel-2 Level-2A tile and one date (walltime is higher)
# specify the path to the tile folder, the path the DEM and the template configuration file (.json)
# First argument is the tile name (nnccc): qsub -v tile="31TCH",date="20170416" runTile_lis_Sentinel2_cluster_muscate_anytile_anydate
# Second argument is the date (YYYMMDD)

# fix the bug with [] in file name
TMPDIR="/tmp/"

# Tile to process
# tile="T"$1
if [ -z $tile ]; then
  echo "tile is not set, exit"
  exit
fi

if [ -z $date ]; then
  echo "date is not set, exit"
  exit
fi

echo $tile " on " $date

# working directory
tmp_output_dir=$TMPDIR/TheiaNeige_Muscate_T${tile}_out/
tmp_input_dir=$TMPDIR/TheiaNeige_Muscate_T${tile}_in/

# storage directory
storage_output_dir=/work/OT/siaa/Theia/Neige/output_muscate_v2_debug/

# S2 L2A products input path
pin="/work/OT/muscate/prod/muscate_prod/data_production/produit/"

# DEM input path
pdem="/work/OT/siaa/Theia/Neige/DEM/"

# input DEM
inputdem=$(find $pdem/S2__TEST_AUX_REFDE2_T${tile}_0001.DBL.DIR/ -name "*ALT_R2.TIF")
echo "inputdem:" $inputdem

# load the available product names from the tile directory
array_zip=($(find $pin/SENTINEL2A_${date}*T${tile}*D* -maxdepth 2 -type f -regex ".*T${tile}.*.zip"))

echo "array size" ${#array_zip[@]}

# use the PBS_ARRAY_INDEX variable to distribute jobs in parallel (bash indexing is zero-based)
i="${array_zip[${PBS_ARRAY_INDEX} - 1]}"

if [ -z $i ]; then
  echo "No file to process PBS_ARRAY_INDEX:" ${PBS_ARRAY_INDEX} 
  exit
fi

echo "array_zip[PBS_ARRAY_INDEX]" $i

# use the product name to identify the config and output files
fzip=$(basename $i)
f=$(basename $i .zip)

echo "fzip" $fzip
echo "f" $f

#create working input directory
pinw=$tmp_input_dir
mkdir -p $pinw

echo "pinw" $pinw

#copy and extract input data

cp $i $pinw
cd $pinw
unzip -u $pinw/$fzip

img_input=$pinw/$f

echo "img_input" $img_input

# create working output directory
pout=$tmp_output_dir/$f/
mkdir -p $pout

echo "pout" $pout

# write the config based on a template file
config=$pout/$f.json
cp /work/OT/siaa/Theia/hpc_scripts/lis_param_Sentinel2_template.json $config

# modify only three parameters: image file, cloud file, dem file, output dir
inputB11=$(find $img_input -name *FRE*B11.tif)
inputB3=$(find $img_input -name *FRE*3.tif)
inputB4=$(find $img_input -name *FRE*B4.tif)
inputcloud=$(find $img_input -name *CLM_R2.tif)

sed -i -e "s|inputB11|$inputB11|g" $config
sed -i -e "s|inputB4|$inputB4|g" $config
sed -i -e "s|inputB3|$inputB3|g" $config
sed -i -e "s|inputcloud|$inputcloud|g" $config
sed -i -e "s|inputdem|$inputdem|g" $config
sed -i -e "s|outputdir|$pout|g" $config

#Load LIS modules
#export MODULEPATH=$MODULEPATH:/work/logiciels/modulefiles_linux3-ci
module load lis/develop

#configure gdal_cachemax to speedup gdal polygonize and gdal rasterize (half of requested RAM)
export GDAL_CACHEMAX=2048

# run the snow detection
date ; echo "START run_snow_detector.py $config"
run_snow_detector.py $config
date ; echo "END run_snow_detector.py"

# copy output to /work
mkdir -p $storage_output_dir/T$tile/
cp -r $pout $storage_output_dir/T$tile/
rm -r $pout $pinw
