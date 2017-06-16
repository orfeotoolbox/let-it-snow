#!/bin/bash
#Script launching LIS on linux3-ci 
#  
#Please setup USER CONFIG for your system before lauching this script
######################USER CONFIG####################################
#####################################################################
#lis app
lis_app=$HOME/lis/run_snow_detector.py
#json template
lis_config=$HOME/lis/config/param_full_Landsat8_template.json
#path where pbs script will be generated 
lis_job_script_PBS=$HOME/lis/pbs/lis_job.pbs
#path where config will be generated
lis_config_list=$HOME/lis/config/config_list.conf
#pbs log
lis_log=$HOME/lis/log
#IO directories
data_input=$DATACI/test_lis/input
data_output=$DATACI/test_lis/output
#tiles to compute
tiles="N2A_France-MetropoleD0005H0001"
#####################################################################

echo "Generating config list..."
rm $lis_config_list
tiles_nb=0
for tile in $tiles
do
pimg=$data_input/$tile
inputdem=$data_input/SRTM/$tile/$tile.tif

for imgdir in $pimg/*
  do    
  #build input config list
  cat << end_configlist >> $lis_config_list
$tile $imgdir $inputdem
end_configlist
  ((tiles_nb++))
  done
done 
echo "Done"
echo "Number of images to compute: $tiles_nb"

echo "Generating pbs script..."
#Create job pbs script
cat << EOF > $lis_job_script_PBS
#!/bin/bash
#PBS -N lis
#PBS -l select=1:ncpus=1
#PBS -l walltime=00:15:00
#PBS -o $lis_log
#PBS -e $lis_log
EOF
if [ $tiles_nb -gt 1 ]
then
  cat << EOF >> $lis_job_script_PBS
#PBS -J 1-${tiles_nb}:1
tile=\$(sed -n \${PBS_ARRAY_INDEX}p $lis_config_list | cut -d ' ' -f1)
imgdir_path=\$(sed -n \${PBS_ARRAY_INDEX}p $lis_config_list | cut -d ' ' -f2)
dem_path=\$(sed -n \${PBS_ARRAY_INDEX}p $lis_config_list | cut -d ' ' -f3)
EOF
else
  cat << EOF >> $lis_job_script_PBS
tile=\$(sed -n 1p $lis_config_list | cut -d ' ' -f1)
imgdir_path=\$(sed -n 1p $lis_config_list | cut -d ' ' -f2)
dem_path=\$(sed -n 1p $lis_config_list | cut -d ' ' -f3)
EOF
fi
cat << EOF >> $lis_job_script_PBS
#copy input data to tmp
#tmp directories
rm -r \$TMPCI/\$(basename \$imgdir_path)_LIS
data_tmp=\$TMPCI/\$(basename \$imgdir_path)_LIS
data_input_tmp=\$data_tmp/input
data_output_tmp=\$data_tmp/output

mkdir -p \$data_input_tmp/\$tile/\$(basename \$imgdir_path)
mkdir -p \$data_input_tmp/SRTM/\$tile

cp -r \$imgdir_path/* $data_input_tmp/\$tile/\$(basename \$imgdir_path)
cp \$dem_path $data_input_tmp/SRTM/\$tile/\$(basename \$dem_path)

imgdir_path=$data_input_tmp/\$tile/\$(basename \$imgdir_path)
dem_path=$data_input_tmp/SRTM/\$tile/\$(basename \$dem_path)

#create json
config=\$imgdir_path.json   
cp $lis_config \$config
# modify only three parameters: image file, cloud file, dem file, output dir
inputimage_green=$(find $dataPath -name *FRE_B3.tif)
inputimage_red=$(find $dataPath -name *FRE_B4.tif)
inputimage_swir=$(find $dataPath -name *FRE_B11.tif)

inputcloud=$(find $dataPath/MASKS/* -name *CLM_R2.tif)
inputdem=$(find $dataPath/SRTM/* -name *ALT_R2.TIF)

pout=$data_output_tmp/\$tile/\$(basename \$imgdir_path)
mkdir -p \$pout

#Create json file in python

#!/usr/bin/python
import json

jsonFile = open("${outputPath}/param_s2_test.json", "r")
data = json.load(jsonFile)
jsonFile.close()

general = data["general"]
general["pout"]="$pout"
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

#run the snow detection
python $lis_app \$config

#copy output files
mkdir -p $data_output/\$tile
cp -r \$pout $data_output/\$tile
cp \$config $data_output/\$tile

EOF

echo "Done"

#lauch qsub
echo "Launching qsub..."
id_job_lis=$(qsub $lis_job_script_PBS)
echo "Done"
echo "LIS ID job: $id_job_lis"


