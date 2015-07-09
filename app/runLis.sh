#!/bin/bash
export PYTHONPATH=/home/grizonnetm/etudes/bin/lis/bin/:$PYTHONPATH

#NEW
#bash runLis.sh /home/grizonnetm/etudes/src/lis/app/param_extract_maroc.json
#bash runLis.sh /home/grizonnetm/etudes/src/lis/app/param_full_maroc.json
#NEW

#visu
#mv2 /home/grizonnetm/data/Output-CES-Neige/final_mask.tif /home/grizonnetm/data/CES-Neige/Baseline/maskfinal_castest.tif /home/grizonnetm/data/Output-CES-Neige/red_nn.tif  /home/grizonnetm/data/CES-Neige/test_CES/Take5/AOI_test_CESNeige/LEVEL2A/Maroc/SPOT4_HRVIR_XS_20130327_N2A_ORTHO_SURF_CORR_PENTE_CMarocD0000B0000.TIF & 

param=$1

output_dir=/home/grizonnetm/data/Output-CES-Neige/

rm -rf $output_dir
mkdir -p $output_dir

python s2snow.py $param 

exit 0
