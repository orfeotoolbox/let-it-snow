#!/bin/bash
#export PYTHONPATH=/home/grizonnetm/etudes/bin/lis/bin/:$PYTHONPATH
source /mnt/data/home/otbtest/config_otb.sh
export PYTHONPATH=/mnt/data/home/gascoins/CES-Neige/build/let-it-snow/bin/:$PYTHONPATH

param=$1

output_dir=/mnt/data/home/gascoins/Output-CES-Neige/

rm -rf $output_dir
mkdir -p $output_dir

python s2snow.py $param 

exit 0
