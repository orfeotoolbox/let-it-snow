#!/bin/sh


#Build a test Json
#INPUTS
#Config path
#LIS data path
#Output path

configPath=$1
dataPath=$2
outputPath=$3

#exit 1 on error
set -e 

# move to config path to build the json file.
cd $configPath

cp param_test_template.json param_test.json

# modify only three parameters: image file, cloud file, dem file, output dir
inputimage=$(find $dataPath -name *ORTHO_SURF_CORR_PENTE*.TIF)
inputcloud=$(find $dataPath -name *NUA.TIF)
inputdem=$(find $dataPath/SRTM/* -name *.tif)
sed -i -e "s|inputimage|$inputimage|g" param_test.json
sed -i -e "s|inputcloud|$inputcloud|g" param_test.json
sed -i -e "s|inputdem|$inputdem|g" param_test.json
sed -i -e "s|outputdir|$outputPath|g" param_test.json
exit 0
 
 
