#!/bin/bash
#PBS -N TheiaNeige
#PBS -j oe
#PBS -l select=1:ncpus=4:mem=20000mb
#PBS -l walltime=08:00:00
#PBS -J 1-135
#PBS -m e
# run LIS for one Sentinel-2 Level-2A tile (all available dates in the tile folder)
# specify the path to the tile folder, the path the DEM and the template configuration file (.json)
# First argument is the tile name (nnccc): qsub -v tile="31TGK",out_path="path/where/to/store/results"(,overwrite="false") runTile_lis_Sentinel2_datalake_anytile.sh

# FIXME: conflict on hal between environnement variable TMPDIR used also internally by openmpi
# Store the directory in  PBS_TMP_DIR
PBS_TMPDIR=$TMPDIR
# Unset TMPDIR env variable which conflicts with openmpi
unset TMPDIR

# Tile to process
# tile="T"$1
if [ -z $tile ]; then
  echo "tile is not set, exit"
  exit 1
fi
echo $tile

if [ -z $overwrite ]; then
  echo "overwrite is not set, not overwrite will be done"
  overwrite="false"
fi

if [ -z $out_path ]; then
  echo "out_path is not set, exit"
  exit 1
fi
echo $out_path

# working directory
tmp_output_dir=$PBS_TMPDIR/TheiaNeige_Muscate_T${tile}_out/
tmp_input_dir=$PBS_TMPDIR/TheiaNeige_Muscate_T${tile}_in/

# storage directory
storage_output_dir=$out_path

# S2 L2A products input path
pin="/datalake/S2-L2A-THEIA/"

# DEM input path
pdem="/work/OT/siaa/Theia/Neige/DEM/"

# input DEM
inputdem=$(find $pdem/S2__TEST_AUX_REFDE2_T${tile}_0001.DBL.DIR/ -name "*ALT_R2.TIF")
echo "inputdem:" $inputdem

# load the available product names from the tile directory
array_products=($(find $pin${tile} -maxdepth 4 -type f -regex ".*T${tile}.*.zip"))
echo "array size" ${#array_products[@]}

# use the PBS_ARRAY_INDEX variable to distribute jobs in parallel (bash indexing is zero-based)
i="${array_products[${PBS_ARRAY_INDEX} - 1]}"

if [ -z $i ]; then
  echo "No file to process PBS_ARRAY_INDEX:" ${PBS_ARRAY_INDEX}
  exit 0
fi

echo "array_products[PBS_ARRAY_INDEX]" $i

# use the product name to identify the config and output files
product_zip=$(basename $i)
product_folder=$(basename $i .zip)

echo "product_folder" $product_folder
echo "product_zip" $product_zip

# check if final folder already exist

if [ -d $storage_output_dir/T$tile/$product_folder ]; then
    echo "$storage_output_dir/T$tile/$product_folder exists!"
    if [ $overwrite == "false" ]; then
        echo "exiting to avoid overwrite"
        exit 1
    fi
fi

#create working input directory
pinw=$tmp_input_dir
mkdir -p $pinw
echo "pinw" $pinw

#copy input data
cp -r $i $pinw/
cd $pinw
unzip -u $pinw/$product_zip

img_input=$pinw/$product_folder
echo "img_input" $img_input

# create working output directory
pout=$tmp_output_dir/$product_folder/
mkdir -p $pout
echo "pout" $pout

#Load LIS modules
#module load lis/develop
source /home/qt/salguesg/load_lis.sh

#configure gdal_cachemax to speedup gdal polygonize and gdal rasterize (half of requested RAM)
export GDAL_CACHEMAX=2048
echo $GDAL_CACHEMAX
export PATH=/home/qt/salguesg/local/bin:/home/qt/salguesg/local/bin:$PATH
echo $PATH

# create config file
date ; echo "START build_json.py $config"
build_json.py -ram 2048 -dem $inputdem $img_input $pout
config=${pout}/param_test.json
echo $config
date ; echo "END build_json.py"

if [ -z "$(ls -A -- $pout)" ]
 then
    echo "ERROR: $pout directory is empty, something wrong happen during build_json"
    exit 1
fi

# run the snow detection
date ; echo "START run_snow_detector.py $config"
run_snow_detector.py $config
date ; echo "END run_snow_detector.py"

# copy output to /work
mkdir -p $storage_output_dir/T$tile/
cp -r $pout $storage_output_dir/T$tile/
rm -r $pout $pinw
