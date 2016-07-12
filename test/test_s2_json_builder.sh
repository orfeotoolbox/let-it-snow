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

cp ${configPath}/param_test_s2_template.json ${outputPath}/param_s2_test.json

# modify only three parameters: image file, cloud file, dem file, output dir
inputimage_green=$(find $dataPath -name *FRE_B3.tif)
inputimage_red=$(find $dataPath -name *FRE_B4.tif)
inputimage_swir=$(find $dataPath -name *FRE_B11.tif)

inputcloud=$(find $dataPath/MASKS/* -name *CLM_R2.tif)
inputdem=$(find $dataPath/SRTM/* -name *ALT_R2.TIF)

temp_python_script=$(mktemp temp_python.XXXX.py)
cat > $temp_python_script <<SCRIPT
#!/usr/bin/python
import json

jsonFile = open("${outputPath}/param_s2_test.json", "r")
data = json.load(jsonFile)
jsonFile.close()

general = data["general"]
general["pout"]="$outputPath"
general["nodata"]="-10000"

inputs = data["inputs"]
inputs["cloud_mask"]="$inputcloud"
inputs["dem"]="$inputdem"

input_green=inputs["green_band"]
input_green["path"]="$inputimage_green"
input_green["noBand"]="1"

input_red=inputs["red_band"]
input_red["path"]="$inputimage_red"
input_red["noBand"]="1"

input_swir=inputs["swir_band"]
input_swir["path"]="$inputimage_swir"
input_swir["noBand"]="1"

jsonFile = open("${outputPath}/param_s2_test.json", "w+")
jsonFile.write(json.dumps(data, indent=4))
jsonFile.close()


SCRIPT

python $temp_python_script

# sed -i -e "s|inputimage|$inputimage|g" ${outputPath}/param_test.json
# sed -i -e "s|inputcloud|$inputcloud|g" ${outputPath}/param_test.json
# sed -i -e "s|inputdem|$inputdem|g" ${outputPath}/param_test.json
# sed -i -e "s|outputdir|$outputPath|g" ${outputPath}/param_test.json


exit 0
 
 
