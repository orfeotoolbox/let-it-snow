#!/bin/bash
#PBS -N TheiaNeige
#PBS -J 1-62:1
#PBS -l select=1:ncpus=1:mem=20000mb
#PBS -l walltime=00:59:00
#PBS -M gascoins@cesbio.cnes.fr
#PBS -m e

# Se positionner  dans le répertoire courant
# PBS_O_WORKDIR correspond au répertoire depuis lequel la commande qsub est lancée
cd "${PBS_O_WORKDIR}"
module load lis/develop

# load the available product names from the tile directory
pin=/work/OT/siaa/Theia/Neige/SNOW_ANNUAL_MAP_LIS_1.5/S2_with_L8_Densification/
inputFiles=($(find $pin -maxdepth 2 -name DAILY_SNOW_MASKS*tif))
echo "array size" ${#inputFiles[@]}

# use the PBS_ARRAY_INDEX variable to distribute jobs in parallel (bash indexing is zero-based)
i="${inputFiles[${PBS_ARRAY_INDEX} - 1]}"

# run script
python ~/Apps/compute_SOD_SMOD.py ${i}
