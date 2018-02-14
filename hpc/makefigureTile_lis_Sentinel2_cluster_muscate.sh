#!/bin/bash
#PBS -N TheiaNViz
#PBS -j oe
#PBS -l select=1:ncpus=4:mem=10gb
#PBS -l walltime=00:35:00
# make output figures for a better vizualisation
# qsub -v tile="29SRQ",input_folder="/work/OT/siaa/Theia/Neige/test_snow_in_cloud_removal" makefigureTile_lis_Sentinel2_cluster_muscate_2.sh
# useful option: qsub -W depend=afterok:<jobid> where jobid is the job id of qsub runTile..

# IM was compiled with openMP in hal
MAGICK_THREAD_LIMIT=4 ; export MAGICK_THREAD_LIMIT
MAGICK_MAP_LIMIT=2000Mb
MAGICK_MEMORY_LIMIT=2000Mb
MAGICK_AREA_LIMIT=2000Mb
export MAGICK_MAP_LIMIT MAGICK_MEMORY_LIMIT MAGICK_AREA_LIMIT
ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=4 ; export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS

# input folder: LIS products path
# Tile to process
if [ -z $input_folder ]; then
  echo "input_folder is not set, exit"
  exit
fi
pin=$input_folder

# output folder: LIS figure path
pout=$pin"/figures/"

# load otb
module load otb

# Tile to process
if [ -z $tile ]; then
  echo "tile is not set, exit"
  exit
fi

# export colored mask in tif using otb
for img in $(find $pin/T$tile/SENTINEL2A*T${tile}*D_V1-0/ -name *SEB.TIF)
do
  echo $img
  tiledate=$(basename $(dirname $(dirname $img)))
  lab=${tiledate:11:8}
  y=${lab:0:4}
  m=${lab:4:2}
  d=${lab:6:2}
  labd=$y-$m-$d
  echo $labd
  pout2=$pout/$tile/$tiledate/$(basename $img .TIF)
  echo $pout2
  mkdir -p $pout2
  imgout=$pout2/$labd.tif
  if [ -f $imgout ]; then
   echo "skip $imgout (already exists)"
  else
   otbcli_ColorMapping -progress false -in $img -out $imgout uint8 -method.custom.lut /work/OT/siaa/Theia/hpc_scripts/LIS_SEB_style_OTB.txt
  fi
#  gdaldem color-relief $img /work/OT/siaa/Theia/hpc_scripts/LIS_SEB_style_v2.txt $imgout -exact_color_entry
done

# export compo in jpg
for img in $(find $pin/T$tile/SENTINEL2A*T${tile}*D_V1-0/ -name *COMPO.TIF)
do
  echo $img
  tiledate=$(basename $(dirname $(dirname $img)))
  lab=${tiledate:11:8}
  y=${lab:0:4}
  m=${lab:4:2}
  d=${lab:6:2}
  labd=$y-$m-$d
  echo $labd
  pout2=$pout/$tile/$tiledate/$(basename $img .TIF)
  echo $pout2
  mkdir -p $pout2
  imgout=$pout2/$labd.jpg
  if [ -f $imgout ]; then
   echo "skip $imgout (already exists)"
  else
   convert -quiet $img $imgout
  fi
done

# make mask montage
montage -geometry 10%x10%+2+2 -label %t -title "$tile Sentinel-2A (cyan: snow,  grey: no snow, white: cloud, black: no data)" -pointsize 40 $pout/$tile/*/LIS_SEB/*.tif $pout/montage_"$tile"_maskcol_onetenthresolution.png

# make compo montage
montage -geometry 10%x10%+2+2 -label %t -title "$tile Sentinel-2A (SWIR false color composites)" -pointsize 40 $pout/$tile/*/LIS_COMPO/*.jpg $pout/montage_"$tile"_compo_onetenthresolution.png
