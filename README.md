# Let-it-snow
## Synopsis

This code is a Python/OTB version of the snow cover extent detection algorithm for Sentinel-2 and Landsat-8 data.

The algorithm documentation with examples is available here:

* [Algorithm theoritical basis documentation](http://tully.ups-tlse.fr/grizonnet/let-it-snow/blob/master/doc/tex/ATBD_CES-Neige.pdf)

To read more about the "Centre d'Expertise Scientifique surface enneigée" (in French):

* [Bulletin THEIA](https://www.theia-land.fr/sites/default/files/imce/BulletinTHEIA3.pdf#page=10)

The input files are Sentinel-2 or Landsat-8 level-2A products from the [Theai Land Data Centre](https://theia.cnes.fr/) or [SPOT-4/5 Take 5 level-2A products](https://spot-take5.org) and the SRTM digital elevation model.

## Code Example

To build DEM data download the SRTM files corresponding to the study area and build the .vrt using gdalbuildvrt. Edit config.json file to activate preprocessing : Set "preprocessing" to true and set the vrt path. 

The snow detection is performed in the Python script app/run_snow_detector.py. 

Configure PYTHONPATH environment
```sh
export PYTHONPATH=${lis-build-dir}/app/:$PYTHONPATH
```
Run the main python script:

```sh
python run_snow_detector param.json
```

There is a Bash script in app directory which allows to set the env variable and run the script:

```sh
runLis.sh param.json
```
## Products format

* COMPO: RGB composition with snow mask 
* SNOW_ALL: Binary mask of snow and clouds.
  * 1st bit: Snow mask after pass1
  * 2nd bit: Snow mask after pass2
  * 3rd bit: Clouds detected at pass0 
  * 4th bit: Clouds refined  at pass0

For example if you want to get the snow from pass1 and clouds detected from pass1 you need to do: 
```python
pixel_value & 00000101  
```
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

Code to generate the snow cover extent product on Theia platform.

## Installation

### Dependencies

lis dependencies: 

GDAL >=2.0
OTB >= 5.0 
Boost-Python
Python interpreter >= 2.7
Python libs >= 2.7
Python packages:
numpy
lxml
matplotlib

GDAL itself depends on a number of other libraries provided by most major operating systems and also depends on the non standard GEOS and PROJ4 libraries. GDAl- Python bindings are also required

Python package dependencies: sys, subprocess, glob, os, json, gdal

### Installing from the source distribution

#### General

In your build directory, use cmake to configure your build.
```sh
cmake -C config.cmake source/lis/
```
In your config.cmake you need to set :
```sh
LIS_DATA_ROOT
```
For OTB superbuild users these cmake variables need to be set:
```sh
OTB_DIR
ITK_DIR
GDAL_INCLUDE_DIR
GDAL_LIBRARY
```
Run make in your build folder.
```sh
make
```
To install s2snow python module. 
In your build folder:
```sh
cd python
python setup.py install
```
or
```sh
python setup.py install --user
```
Update environment variables for LIS. Make sure that OTB and other dependencies directories are set in your environment variables:
```sh
export PYTHONPATH=/your/build/directory/bin/:$PYTHONPATH
export PATH=/your/build/directory/bin:$PATH
```
let-it-snow is now installed.

#### On venuscalc

To configure OTB 5.2.1:

Create a bash file which contains:
```sh
source /mnt/data/home/otbtest/config_otb_5.2.1.sh
```

Then build the lis project using cmake
```sh
cd $build_dir
cmake -DCMAKE_CXX_FLAGS:STRING=-std=c++11 -DCMAKE_CXX_COMPILER:FILEPATH=/usr/bin/g++-4.8 -DCMAKE_C_COMPILER:FILEPATH=/usr/bin/gcc-4.8 -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DGDAL_INCLUDE_DIR=/mnt/data/home/otbtest/OTB/SuperBuild/include -DGDAL_LIBRARY=/mnt/data/home/otbtest/OTB/SuperBuild/lib/libgdal.so $source_dir
make
```
To install s2snow python module. 
In your build folder:
```sh
cd python
python setup.py install
```
or
```sh
python setup.py install --user
```
Update environment variables for LIS. Make sure that OTB and other dependencies directories are set in your environment variables:
```sh
export PYTHONPATH=/your/build/directory/bin/:$PYTHONPATH
export PATH=/your/build/directory/bin:$PATH
```
let-it-snow is now installed.

## Tests

Enable tests with BUILD_TESTING cmake option. Use ctest to run tests. Do not forget to clean your output test directory when you run a new set of tests.

Download LIS-Data folder. It contains all the data needed to run tests. Set Data-LIS path var in cmake configuration files. 
Baseline : Baseline data folder. It contains output files of S2Snow that have been reviewed and validated. 
Data-Test : Test data folder needed to run tests. It contains Landsat, Take5 and SRTM data.
Output-Test : Temporary output tests folder.
Do not modify these folders.

## Contributors

Manuel Grizonnet (CNES), Simon Gascoin (CNRS/CESBIO), Tristan Klempka (CNES)

## License

This is free software under the GPL v3 licence. See
http://www.gnu.org/licenses/gpl-3.0.html for details.
