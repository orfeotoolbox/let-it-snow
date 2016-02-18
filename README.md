# CES NeigeOA
## Synopsis

This code is a Python/OTB version of the demonstrator of the snow detection algorithm for Sentinel-2 images. 

To read more about this product (in French):

* [Bulletin THEIA](https://www.theia-land.fr/sites/default/files/imce/BulletinTHEIA3_light.pdf#page=10)

* [Slides Séminaire GEOSUD](http://www.equipex-geosud.fr/documents/10180/233868/7_GascoinHagolle2015-THEIA+CES+surface+enneigee_S%C3%A9minaire+Theia+Geosud+2015.pdf)

The input files are SPOT-4 or Landsat-8 Level-2A images from Theia Land and the SRTM digital elevation model.

## Code Example

To build DEM data. Download VRT files corresponding to the data and build the .vrt using gdalbuildvrt. Edit config.json file to activate preprocessing : Set "preprocessing" to true and set vrt path. It will  project and resample the SRTM DEM over the Landsat/SPOT area (30m:Landsat8 or 20m:Take5). It uses gdalwarp with the cubicspline option.
The snow detection is performed in the Python script app/S2Snow.py. 

```
Configure PYTHONPATH environnement
export PYTHONPATH=${lis-build-dir}/bin/:$PYTHONPATH
```
Run the main python script:

```
python s2snow.py param.json
```

There is a Bash script in app directory which allows to set the env variable and run the script:

```
runLis.sh param.json
```

## Motivation

Code to generate CES Neige products on Theia platforms

## Installation

### Dependencies

lis dependencies: 

GDAL >=1.9
OTB >= 5.0 
Boost-Python
Python interpreter >= 2.7
Python libs >= 2.7

GDAL itself depends on a number of other libraries provided by most major operating systems and also depends on the non standard GEOS and PROJ4 libraries. GDAl- Python bindings are also required

Python package dependencies: sys, subprocess, glob, os, json, gdal

### Installing from the source distribution

To configure OTB on venuscalc:

source /mnt/data/home/otbtest/config_otb.sh

### Then build the lis project using cmake
````
cd $build_dir
cmake -DCMAKE_CXX_FLAGS:STRING=-std=c++11 -DCMAKE_CXX_COMPILER:FILEPATH=/usr/bin/g++-4.8 -DCMAKE_C_COMPILER:FILEPATH=/usr/bin/gcc-4.8 -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DGDAL_INCLUDE_DIR=/mnt/data/home/otbtest/OTB/SuperBuild/include -DGDAL_LIBRARY=/mnt/data/home/otbtest/OTB/SuperBuild/lib/libgdal.so $source_dir
make
````
## Tests

Download LIS-Data folder. It contains all the data needed to run tests. Set Data-LIS path var in cmake configuration files. 
Baseline : Baseline data folder. It contains output files of S2Snow that have been reviewed and validated. 
Data-Test : Test data folder needed to run tests. It contains Landsat, Take5 and SRTM data.
Output-Test : Temporary output tests folder.
Do not modify these folders.
Enable tests with BUILD_TESTING cmake option

## Contributors

Manuel Grizonnet (CNES), Simon Gascoin (CNRS/CESBIO), Tristan Klempka (Stagiaire CNES)

## License

This is free software under the GPL v3 licence. See
http://www.gnu.org/licenses/gpl-3.0.html for details.

