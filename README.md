## Synopsis

This code is a Python/OTB version of the demonstrator of the snow detection algorithm for Sentinel-2 images.

The input files were generated from L2 images downloaded from Theia Land and pre-processed by three shell scripts:

    decompresse_*.sh, to unzip the files
    decoupe_*.sh, to extract a rectangle AOI from L2A data using gdal_translate with projection window defined in the ascii file AOI_test_CESNeige.csv
    projette_mnt_*.sh, to project the SRTM DEM and resample at 30m or 20m (Landsat8 or Take5) over the same AOI. It uses gdalwarp with the cubicspline option

Thenn the snow detection is performed in a Python script.

## Code Example

Configure PYTHONPATH environnement
export PYTHONPATH=${lis-build-dir}/bin/:$PYTHONPATH

Run the main python script:

python s2snow.py param.json

There is a Bash script in app directory which allows to set the env variable and run the script:

runLis.sh param.json

## Motivation

Code to generate CES Neige products on theia platforms

## Installation

### Dependencies

lis dependencies: 

GDAL >=1.9
OTB >= 5.0 
Boost-Python
Python interpreter >= 2.7
Python libs >= 2.7

GDAL itself depends on a number of other libraries provided by most major operating systems and also depends on the non standard GEOS and PROJ4 libraries. GDAl- Python bindings are also required

Python package dependencies:sys, subprocess,glob,os,json,gdal

## Installing from the source distribution

to configure OTB on venus calc:

source /mnt/data/home/otbtest/config_otb.sh

# Then build the lis project using cmake

cd $build_dir
cmake -DCMAKE_CXX_FLAGS:STRING=-std=c++11 -DCMAKE_CXX_COMPILER:FILEPATH=/usr/bin/g++-4.8 -DCMAKE_C_COMPILER:FILEPATH=/usr/bin/gcc-4.8 -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON $source_dir
make

## Tests

Unable tests with BUILD_TESTING cmake option

## Contributors

Manuel Grizonnet (CNES), Simon Gascoin (CNRS)

## License

This is free software under the GPL v3 licence. See
http://www.gnu.org/licenses/gpl-3.0.html for details.

