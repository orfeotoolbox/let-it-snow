# Run LIS from SEN2COR Level 2A product

This tutorial demonstrates how to run the LIS algorithm (Let It Snow) to produce
Snow surface products from the output of the SEN2COR.

[lis_from_maja.md](http://tully.ups-tlse.fr/grizonnet/let-it-snow/blob/develop/doc/tutorials/lis_from_maja.md)

**WARNING: LIS develop branch was used to write the tutorial. Note that utility
 script in LIS version 1.4 are not fully compatible with MAJA native format.**

## Generate LIS JSON parameters using build_json.py

Download SEN3COR Level 2A products from any providers (scihub for instance).

In my case, I have a directory called:

```
S2A_MSIL2A_20180311T075731_N0206_R035_T38SLH_20180311T101707.SAFE
```

The DTM on the same area came be any DTM. The only requirement is that it should contains the Sentinel tile. It can be of any resolution as it will be resample internally by LIS preprocessing step.

We're going to use the utilities script [build_json.py](http://tully.ups-tlse.fr/grizonnet/let-it-snow/blob/develop/app/build_json.py)
which allows to configure LIS and generates the parameter file (JSON
format).

This script takes as input the directory which contains the surface reflectance
images, the output directory where the JSON file will be stored.Sensors,
filenames, band numbers, cloud mask encoding are automatically automatically
retrieved from the directory name and structures.


In the case of the Sentinel2 over Mount Artos tile, the command is:

```
uild_json.py -dem  /media/grizonnetm/My\ Passport/DATA/S2/SEN2COR/ARTOS/DTM/srtm_45_05.tif -preprocessing true -nodata 0 /media/grizonnetm/My\ Passport/DATA/S2/SEN2COR/ARTOS/S2A_MSIL2A_20180311T075731_N0206_R035_T38SLH_20180311T101707.SAFE/ /media/grizonnetm/My\ Passport/DATA/S2/SEN2COR/ARTOS/LIS-TEST/
```
The important parameter here is 'preprocessing' which should be set to 'true' to activate the DTM resampling. It is not necessary with MAJA native products as the 'prepare_mnt' processor already resample the DTM at the resolution and over the same geographic area as the Sentinel image.


The output json file is called **param_test.json**. (Hopefully we will change to a
more comprehensive name in the future).

Note that the generated JSON file will use default parameters of the LIS
processor. You can overload all parameters with build_json.py command line
parameters.

## Run LIS

Then you can run the **run_snow_detector.py** script to generate Snow Surface
product:

```
run_snow_detector.py output_dir_lis/param_test.json
```

LIS products are available in LIS_PRODUCTS sub-directory.

![alt text](images/artos-lis-compo-sen2cor.png "Mount Artos SEN2COR Sentinel-2A
Snow detection result")
