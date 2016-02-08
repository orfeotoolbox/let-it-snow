#!/bin/bash
#export PYTHONPATH=/home/grizonnetm/etudes/bin/lis/bin/:$PYTHONPATH

#source /mnt/data/home/otbtest/config_otb.sh
export PYTHONPATH=/home/grizonnetm/etudes/bin/lis/bin/:$PYTHONPATH

param=$1

output_dir=/home/grizonnetm/temporary/Output-CES-Neige

rm -rf $output_dir
mkdir -p $output_dir

python s2snow.py $param 

exit 0
