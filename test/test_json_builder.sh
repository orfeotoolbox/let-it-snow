#!/bin/sh


#Build a test Json
#INPUTS
#Config path
#LIS data path
#Output path

configPath=$1
dataPath=$2
outputPath=$3

echo $1
echo $2
echo $3

#exit 1 on error
set -e 

#create output directory
mkdir -p $outputPath

# move to config path to build the json file.

cp ${configPath}/param_test_template.json ${outputPath}/param_test.json

# modify only three parameters: image file, cloud file, dem file, output dir
inputimage=$(find $dataPath -name *ORTHO_SURF_CORR_PENTE*.TIF)
inputcloud=$(find $dataPath -name *NUA.TIF)
inputdem=$(find $dataPath/SRTM/* -name *.tif)

echo $inputdem

temp_python_script=$(mktemp temp_python.XXXX.py)
cat > $temp_python_script <<SCRIPT
#!/usr/bin/python
import json

jsonFile = open("${outputPath}/param_test.json", "r")
data = json.load(jsonFile)
jsonFile.close()

general = data["general"]
general["pout"]="$outputPath"
general["nodata"]="-10000"

inputs = data["inputs"]
inputs["cloud_mask"]="$inputcloud"
inputs["dem"]="$inputdem"

input_green=inputs["green_band"]
input_green["path"]="$inputimage"
input_green["noBand"]="1"

input_red=inputs["red_band"]
input_red["path"]="$inputimage"
input_red["noBand"]="2"

input_swir=inputs["swir_band"]
input_swir["path"]="$inputimage"
input_swir["noBand"]="4"

jsonFile = open("${outputPath}/param_test.json", "w+")
jsonFile.write(json.dumps(data, indent=4))
jsonFile.close()


SCRIPT

python $temp_python_script

# sed -i -e "s|inputimage|$inputimage|g" ${outputPath}/param_test.json
# sed -i -e "s|inputcloud|$inputcloud|g" ${outputPath}/param_test.json
# sed -i -e "s|inputdem|$inputdem|g" ${outputPath}/param_test.json
# sed -i -e "s|outputdir|$outputPath|g" ${outputPath}/param_test.json

rm $temp_python_script

exit 0
 
 
