# CES NeigeOA
## Synopsis

This code is a Python/OTB version of the demonstrator of the snow detection algorithm for Sentinel-2 images. 

To read more about this product (in French):

* [Bulletin THEIA](https://www.theia-land.fr/sites/default/files/imce/BulletinTHEIA3_light.pdf#page=10)

* [Slides Séminaire GEOSUD](http://www.equipex-geosud.fr/documents/10180/233868/7_GascoinHagolle2015-THEIA+CES+surface+enneigee_S%C3%A9minaire+Theia+Geosud+2015.pdf)

The input files are SPOT  or Landsat-8 Level-2A images from Theia Land and the SRTM digital elevation model.

## Code Example

To build DEM data. Download VRT files corresponding to the data and build the .vrt using gdalbuildvrt. Edit config.json file to activate preprocessing : Set "preprocessing" to true and set vrt path. It will project and resample the SRTM DEM over the Landsat/SPOT area (30m:Landsat8 or 20m:Take5). It uses gdalwarp with the cubicspline option.

The snow detection is performed in the Python script app/run_snow_detector.py. 

```
Configure PYTHONPATH environnement
export PYTHONPATH=${lis-build-dir}/app/:$PYTHONPATH
```
Run the main python script:

```
python run_snow_detector param.json
```

There is a Bash script in app directory which allows to set the env variable and run the script:

```
runLis.sh param.json
```
## Products format

* COMPO: RGB composition with snow mask 
* SNOW_ALL: Binary mask of snow and clouds.
  * 1st bit: Snow detected from pass1
  * 2nd bit: Snow detected from pass2
  * 3rd bit: Clouds detected from pass1 
  * 4th bit: Clouds refined  from pass2

For example if you want to get the snow from pass1 and clouds detected from pass1 you need to do: 
````
pixel_value & 00000101  
````
* SEB: Raster image of the snow mask and cloud mask. 
  * 0: No-snow
  * 100: Snow
  * 205: Cloud including cloud shadow
  * 254: No data
* SEB_VEC: Vector image of the snow mask and cloud mask. Two fields of information are embbeded in this product. DN (for Data Neige) and type.
  * DN field :
     * 0: No-snow
     * 100: Snow
     * 205: Cloud including cloud shadow
     * 254: No data
  * Type field:
     * no-snow
     * snow
     * cloud
     * no-data

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

#### General

In your build directory, use cmake to configure your build.
```` 
cmake -C config.cmake source/lis/
````
In your config.cmake you need to set :
````
LIS_DATA_ROOT
````
For OTB superbuild users these cmake variables need to be set:
````
OTB_DIR
ITK_DIR
GDAL_INCLUDE_DIR
GDAL_LIBRARY
````
Run make in your build folder.
````
make
````
To install s2snow python module. 
In your build folder:
````
cd python
python setup.py install
```` 
or
````
python setup.py install --user
````
Update LD_LIBRARY_PATH. Make sure that OTB and other dependencies directories are set in your environment variables:
````
export LD_LIBRARY_PATH=/let-it-snow/build/folder/bin/:$LD_LIBRARY_PATH
````
let-it-snow is now installed.

#### On venuscalc

To configure OTB :
````
source /mnt/data/home/otbtest/config_otb.sh
````
Then build the lis project using cmake
````
cd $build_dir
cmake -DCMAKE_CXX_FLAGS:STRING=-std=c++11 -DCMAKE_CXX_COMPILER:FILEPATH=/usr/bin/g++-4.8 -DCMAKE_C_COMPILER:FILEPATH=/usr/bin/gcc-4.8 -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DGDAL_INCLUDE_DIR=/mnt/data/home/otbtest/OTB/SuperBuild/include -DGDAL_LIBRARY=/mnt/data/home/otbtest/OTB/SuperBuild/lib/libgdal.so $source_dir
make
````
To install s2snow python module. 
In your build folder:
````
cd python
python setup.py install
```` 
or
````
python setup.py install --user
````
Update LD_LIBRARY_PATH. Make sure that OTB and other dependencies directories are set in your environment variables:
````
export LD_LIBRARY_PATH=/let-it-snow/build/folder/bin/:$LD_LIBRARY_PATH
````

let-it-snow is now installed.

## Tests

Enable tests with BUILD_TESTING cmake option. Use ctest to run tests. Do not forget to clean your output test directory when you run a new set of tests.

Download LIS-Data folder. It contains all the data needed to run tests. Set Data-LIS path var in cmake configuration files. 
Baseline : Baseline data folder. It contains output files of S2Snow that have been reviewed and validated. 
Data-Test : Test data folder needed to run tests. It contains Landsat, Take5 and SRTM data.
Output-Test : Temporary output tests folder.
Do not modify these folders.

## Contributors

Manuel Grizonnet (CNES), Simon Gascoin (CNRS/CESBIO), Tristan Klempka (Stagiaire CNES)

## License

This is free software under the GPL v3 licence. See
http://www.gnu.org/licenses/gpl-3.0.html for details.