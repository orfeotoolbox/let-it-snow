#!/bin/bash
#Script launching LIS cloud removal on linux3-ci 
#  
#Please setup USER CONFIG for your system before lauching this script
######################USER CONFIG####################################
#####################################################################
#lis app
lis_app=$HOME/lis/run_cloud_removal.py
#json template
lis_config=$HOME/lis/config/param_cloudremoval_template.json
#path where pbs script will be generated 
lis_job_script_PBS=$HOME/lis/pbs/lis_job_cr.pbs
#path where config will be generated
lis_config_list=$HOME/lis/config/config_list_cr.conf
#pbs log
lis_log=$HOME/lis/log
#IO directories
data_input=$DATACI/test_cloudremoval/input
data_output=$DATACI/test_cloudremoval/output
#tiles to compute
tiles="N2A_EcrinsFranceD0000B0000"
stats=false
hsmin=2500
hsmax=3700
#####################################################################

echo "Generating config list..."
rm $lis_config_list
tiles_nb=0
for tile in $tiles
do
pimg=$data_input/$tile
inputdem=$data_input/SRTM/$tile/$tile.tif

imgarr=($pimg/*)
imgnb=$(find $pimg -mindepth 1 -maxdepth 1 -type d | wc -l)
slicemax=$(($imgnb-2))

for i in `seq 2 $slicemax`
do
    echo "$tile $inputdem ${imgarr[$i-2]} ${imgarr[$i-1]} ${imgarr[$i]} ${imgarr[$i+1]} ${imgarr[$i+2]}" >> $lis_config_list
    ((tiles_nb++))
done 
done

echo "Done"
echo "Number of images to compute: $tiles_nb"

echo "Generating pbs script..."
#Create pbs job script
cat <<EOF > $lis_job_script_PBS
#!/bin/bash
#PBS -N lis
#PBS -l select=1:ncpus=1
#PBS -l walltime=00:45:00
#PBS -o $lis_log
#PBS -e $lis_log
#PBS -J 1-${tiles_nb}:1

tile=\$(sed -n \${PBS_ARRAY_INDEX}p $lis_config_list | cut -d ' ' -f1)
dempath=\$(sed -n \${PBS_ARRAY_INDEX}p $lis_config_list | cut -d ' ' -f2)
m2path=\$(sed -n \${PBS_ARRAY_INDEX}p $lis_config_list | cut -d ' ' -f3)
m1path=\$(sed -n \${PBS_ARRAY_INDEX}p $lis_config_list | cut -d ' ' -f4)
t0path=\$(sed -n \${PBS_ARRAY_INDEX}p $lis_config_list | cut -d ' ' -f5)
p1path=\$(sed -n \${PBS_ARRAY_INDEX}p $lis_config_list | cut -d ' ' -f6)
p2path=\$(sed -n \${PBS_ARRAY_INDEX}p $lis_config_list | cut -d ' ' -f7)

#copy input data to tmp
#tmp directories
rm -r \$TMPCI/\$(basename \$t0path)_LIS_cr
data_tmp=\$TMPCI/\$(basename \$t0path)_LIS_cr
data_input_tmp=\$data_tmp/input
data_output_tmp=\$data_tmp/output

mkdir -p \$data_input_tmp/\$tile/\$(basename \$t0path)
mkdir -p \$data_input_tmp/SRTM/\$tile

cp -r \$t0path/* \$data_input_tmp/\$tile/\$(basename \$t0path)
cp \$dempath \$data_input_tmp/SRTM/\$tile/\$(basename \$dempath)

t0path=\$data_input_tmp/\$tile/\$(basename \$t0path)
dempath=\$data_input_tmp/SRTM/\$tile/\$(basename \$dempath)

#create json
config=\$t0path.json
cp $lis_config \$config

#modify json
m2img=\$(find \$m2path -name *SEB.TIF)
m1img=\$(find \$m1path -name *SEB.TIF)
t0img=\$(find \$t0path -name *SEB.TIF)
p1img=\$(find \$p1path -name *SEB.TIF)
p2img=\$(find \$p2path -name *SEB.TIF)
pout=\$data_output_tmp/\$tile/\$(basename \$t0path)
mkdir -p \$pout
sed -i -e "s|outputdir|\$pout|g" \$config
sed -i -e "s|m2path|\$m2img|g" \$config
sed -i -e "s|m1path|\$m1img|g" \$config
sed -i -e "s|t0path|\$t0img|g" \$config
sed -i -e "s|p1path|\$p1img|g" \$config
sed -i -e "s|p2path|\$p2img|g" \$config
sed -i -e "s|dempath|\$dempath|g" \$config
sed -i -e "s|hsmax|$hsmax|g" \$config
sed -i -e "s|hsmin|$hsmin|g" \$config

#run cloud removal
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
echo "LIS cr ID job: $id_job_lis"
