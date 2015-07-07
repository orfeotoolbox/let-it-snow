#!/bin/bash
export PYTHONPATH=/home/grizonnetm/etudes/bin/lis/bin/:$PYTHONPATH

#NEW
#bash runLis.sh /home/grizonnetm/etudes/src/lis/app/param_extract_maroc.json
#bash runLis.sh /home/grizonnetm/etudes/src/lis/app/param_full_maroc.json
#NEW

param=$1

output_dir=/home/grizonnetm/data/Output-CES-Neige/

rm -rf $output_dir
mkdir -p $output_dir

python s2snow.py $param 

exit 0
