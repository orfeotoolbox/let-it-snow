#!/bin/bash
export PYTHONPATH=/home/grizonnetm/etudes/bin/lis/bin/:$PYTHONPATH

#NEW
#bash runLis.sh /home/grizonnetm/etudes/src/lis/scripts/param_extract_maroc.json
#NEW

#bash runLis.sh /home/grizonnetm/data/CES-Neige/test_CES/Take5/AOI_test_CESNeige/LEVEL2A/Maroc/SPOT4_HRVIR_XS_20130327_N2A_ORTHO_SURF_CORR_PENTE_CMarocD0000B0000.TIF /home/grizonnetm/data/CES-Neige/test_CES/Take5/AOI_test_CESNeige/SRTM/Maroc/Maroc.tif /home/grizonnetm/data/CES-Neige/test_CES/Take5/AOI_test_CESNeige/LEVEL2A/Maroc/SPOT4_HRVIR_XS_20130327_N2A_CMarocD0000B0000_NUA.TIF /home/grizonnetm/etudes/src/lis/scripts/param_extract_maroc.json

#bash runLis.sh /home/grizonnetm/data/CES-Neige/Data_Full/SPOT4_HRVIR_XS_20130327_N2A_CMarocD0000B0000/SPOT4_HRVIR_XS_20130327_N2A_ORTHO_SURF_CORR_PENTE_CMarocD0000B0000.TIF /home/grizonnetm/data/CES-Neige/Data_Full/SRTM/srtm_superimpose.tif /home/grizonnetm/data/CES-Neige/Data_Full/SPOT4_HRVIR_XS_20130327_N2A_CMarocD0000B0000/MASK/SPOT4_HRVIR_XS_20130327_N2A_CMarocD0000B0000_NUA.TIF 



# data_dir=/home/grizonnetm/data/CES-Neige/test_CES/Take5/AOI_test_CESNeige
# img=$data_dir/LEVEL2A/Maroc/SPOT4_HRVIR_XS_20130327_N2A_ORTHO_SURF_CORR_PENTE_CMarocD0000B0000.TIF
# dem=$data_dir/SRTM/Maroc/Maroc.tif
# cloud=$data_dir/LEVEL2A/Maroc/SPOT4_HRVIR_XS_20130327_N2A_CMarocD0000B0000_NUA.TIF

img=$1
dem=$2
cloud=$3
param=$1

output_dir=/home/grizonnetm/data/Output-CES-Neige/

rm -rf $output_dir
mkdir -p $output_dir

python s2snow.py $param 

exit 0
