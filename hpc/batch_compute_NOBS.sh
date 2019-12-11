#!/bin/bash
#PBS -N TheiaNeige
#PBS -J 1-191:1
#PBS -l select=1:ncpus=1:mem=20000mb
#PBS -l walltime=00:59:00
#PBS -M gascoins@cesbio.cnes.fr
#PBS -m e

# Load lis environnment 
module load lis/develop

# Load all the available product names from the tile directory
pin=/work/OT/siaa/Theia/Neige/SNOW_ANNUAL_MAP_LIS_1.5/S2_with_L8_Densification/
inputFiles=($(find $pin -name multitemp_cloud_mask.vrt))

# use the PBS_ARRAY_INDEX variable to distribute jobs in parallel (bash indexing is zero-based)
i="${inputFiles[${PBS_ARRAY_INDEX} - 1]}"

# run script
python "${PBS_O_WORKDIR}"/compute_NOBS.py ${i}
