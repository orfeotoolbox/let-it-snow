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

#tmp directories
data_tmp=$TMPCI/test_lis
data_input_tmp=$data_tmp/input
data_input_dem_tmp=$data_input_tmp/SRTM
data_output_tmp=$data_tmp/output
echo "Generating pbs script..."
#Create job pbs script
cat << EOF > $lis_job_script_PBS
#!/bin/bash
#PBS -N lis
#PBS -l select=1:ncpus=1
#PBS -l walltime=00:08:00
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

rm -r $data_tmp
mkdir -p $data_tmp
mkdir -p $data_input_tmp/\$tile/\$(basename \$imgdir_path)
mkdir -p $data_input_tmp/SRTM/\$tile

cp -r \$imgdir_path $data_input_tmp/\$tile/\$(basename \$imgdir_path)
cp -r \$dem_path $data_input_tmp/SRTM/\$tile/\$(basename \$dem_path)

imgdir_path=$data_input_tmp/\$tile/\$(basename \$imgdir_path)
dem_path=$data_input_tmp/SRTM/\$tile/\$(basename \$dem_path)

#create json
config=\$imgdir_path.json   
cp $lis_config \$config
# modify only three parameters: image file, cloud file, dem file, output dir
inputimage=\$(find \$imgdir_path -name *ORTHO_SURF_CORR_PENTE*.TIF)
inputcloud=\$(find \$imgdir_path -name *NUA.TIF)
inputdem=\$dem_path
mkdir -p $data_output_tmp/\$tile
pout=$data_output_tmp/\$tile/\$(basename \$imgdir_path)
mkdir -p \$pout
sed -i -e "s|inputimage|\$inputimage|g" \$config
sed -i -e "s|inputcloud|\$inputcloud|g" \$config
sed -i -e "s|inputdem|\$inputdem|g" \$config
sed -i -e "s|outputdir|\$pout|g" \$config

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


