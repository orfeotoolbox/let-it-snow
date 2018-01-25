# Let-it-snow
## Synopsis

This code implements the snow cover extent detection algorithm LIS (Let It Snow) for Sentinel-2, Landsat-8 and SPOT4-Take5 data.

The algorithm documentation with examples is available here:

* [Algorithm theoretical basis documentation](http://tully.ups-tlse.fr/grizonnet/let-it-snow/blob/master/doc/tex/ATBD_CES-Neige.pdf)

To read more about the "Centre d'Expertise Scientifique surface enneigée" (in French):

* [Bulletin THEIA](https://www.theia-land.fr/sites/default/files/imce/BulletinTHEIA3.pdf#page=10)

The input files are Sentinel-2 or Landsat-8 level-2A products from the [Theai Land Data Centre](https://theia.cnes.fr/) or [SPOT-4/5 Take 5 level-2A products](https://spot-take5.org) and the SRTM digital elevation model reprojected at the same resolution as the input image.

##Usage

Run the python script run_snow_detector.py with a json configuration file as unique argument:

```bash
python run_snow_detector.py param.json
```
The snow detection is performed in the Python script [run_snow_detector.py](app/run_snow_detector.py).

All the parameters of the algorithm, paths to input and output data are stored in the json file. See the provided example [param_test_s2_template.json](tes/param_test_s2_template.json) file for an example.

Moreover The JSON schema is available in the [Algorithm theoritical basis documentation](doc/tex/ATBD_CES-Neige.tex) and gives more information about the roles of these parameters.

NB: To build DEM data download the SRTM files corresponding to the study area and build the .vrt using gdalbuildvrt. Edit config.json file to activate preprocessing : Set "preprocessing" to true and set the vrt path.


## Products format

* COMPO: Raster image showing the outlines of the cloud (including cloud shadow) and snow masks drawn on the RGB composition of the L2A image (bands SWIR/Red/Green).
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

## Data set example

Sequence of snow maps produced from Sentinel-2 type of observations (SPOT-5 Take 5) over the Deux Alpes and Alpe d'Huez ski resorts are available on [Zenodo](http://doi.org/10.5281/zenodo.159563).

## Motivation

Code to generate the snow cover extent product on Theia platform.

## Installation

LIS processing chain uses CMake (http://www.cmake.org) for building from source.

### Dependencies

Following a summary of the required dependencies: 

* GDAL >=2.0
* OTB >= 6.0
* Python interpreter >= 2.7
* Python libs >= 2.7
* Python packages:
* numpy
* lxml
* matplotlib

GDAL itself depends on a number of other libraries provided by most major operating systems and also depends on the non standard GEOS and PROJ4 libraries. GDAl- Python bindings are also required

Python package dependencies:

* sys
* subprocess
* glob
* os
* json
* gdal

Optional dependencies:

* gdal_trace_outline can be used alternatively to gdal_polygonize.py to generate the vector layer. It requires to install [dans-gdal-scripts utilities](https://github.com/gina-alaska/dans-gdal-scripts).

### Installing from the source distribution

#### General

In your build directory, use cmake to configure your build.
```bash
cmake -C config.cmake source/lis/
```
In your config.cmake you need to set :
```bash
LIS_DATA_ROOT
```
For OTB superbuild users these cmake variables need to be set:
```bash
OTB_DIR
ITK_DIR
GDAL_INCLUDE_DIR
GDAL_LIBRARY
```
Run make in your build folder.
```bash
make
```
To install let-it-snow application and the s2snow python module.
In your build folder:
```bash
make install
```

Add appropriate executable rights
```bash
chmod -R 755 ${install_dir}
```

The files will be installed by default into /usr/local and add to the python default modules.
To overide this behavior, the variable CMAKE_INSTALL_PREFIX must be configure before build step.

Update environment variables for LIS. Make sure that OTB and other dependencies directories are set in your environment variables:
```bash
export PATH=/your/install/directory/bin:/your/install/directory/app:$PATH
export LD_LIBRARY_PATH=/your/install/directory/lib:$LD_LIBRARY_PATH
export OTB_APPLICATION_PATH=/your/install/directory/lib:$OTB_APPLICATION_PATH
export PYTHONPATH=/your/install/directory/lib:/your/install/directory/lib/python2.7/site-packages:$PYTHONPATH
```
let-it-snow is now installed.

## Tests

Enable tests with BUILD_TESTING cmake option. Use ctest to run tests. Do not forget to clean your output test directory when you run a new set of tests.

Data (input and baseline) to run validation tests are available on [Zenodo](http://doi.org/10.5281/zenodo.166511).

Download LIS-Data and extract the folder. It contains all the data needed to run tests. Set Data-LIS path var in cmake configuration files.
Baseline : Baseline data folder. It contains output files of S2Snow that have been reviewed and validated.
Data-Test : Test data folder needed to run tests. It contains Landsat, Take5 and SRTM data.
Output-Test : Temporary output tests folder.
Do not modify these folders.

## Contributors

Manuel Grizonnet (CNES), Simon Gascoin (CNRS/CESBIO), Tristan Klempka (CNES), Germain Salgues (Magellium)

## License

This is free software under the GNU Affero General Public License v3.0. See
http://www.gnu.org/licenses/agpl.html for details.
