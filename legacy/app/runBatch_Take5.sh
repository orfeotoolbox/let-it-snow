#!/bin/bash
#export PYTHONPATH=/home/grizonnetm/etudes/bin/lis/bin/:$PYTHONPATH
source /mnt/data/home/otbtest/config_otb.sh
export PYTHONPATH=/mnt/data/home/gascoins/CES-Neige/build/let-it-snow/bin/:$PYTHONPATH

output_dir=/mnt/data/home/gascoins/Take5/Output-CES-Neige

# main input path 
pin="/mnt/data/home/gascoins/Take5/"

# Path to DEM
pdem=$pin/"SRTM"

# Tiles to process
tiles="CAlpes CMaroc CSudmipy-E CSudmipy-O"

for tile in $tiles
do

# Path to tiles
pimg=$pin/$tile"_LEVEL2A"

# input DEM
inputdem=$pdem/$tile/$tile.tif

for i in $pimg/*
  do

  # write the config based on a template file
  cp ../config/param_full_Take5_template.json tmp.json

  # modify only three parameters: image file, cloud file, dem file, output dir
  inputimage=$(find $i -name *ORTHO_SURF_CORR_PENTE*.TIF)
  inputcloud=$(find $i -name *NUA.TIF)
  pout=$output_dir/$tile/$(basename $i)
  sed -i -e "s|inputimage|$inputimage|g" tmp.json
  sed -i -e "s|inputcloud|$inputcloud|g" tmp.json
  sed -i -e "s|inputdem|$inputdem|g" tmp.json
  sed -i -e "s|outputdir|$pout|g" tmp.json

  # creates the output directory
  mkdir -p $pout

  # run the snow detection
  python s2snow.py tmp.json

  # backup config file
  mv tmp.json $pout

  done
done 

exit 0

