# Run Let It Snow from MAJA

This tutorial demonstrates how to run the LIS algorithm (Let It Snow) to
produce Snow surface products from the output of the MAJA processor
(with MAJA native format).

## Run MAJA

The MAJA processor (MACCS ATCOR Joint Algorithm, say "maya") is the state of the
art for cloud detection and atmospheric correction, specifically designed to
process time series of optical images at high resolution, acquired under quasi
constant viewing angles. It allows for instance to process time series of
LANDSAT or Sentinel-2 images.

The delivered version of MAJA can ingest L1 products int the following formats
(delivered in the package):

- Sentinel-2: (PSD) S2-PDGS-TAS-DI-PSD  v.12 AND v.14.2
- Landsat8: Landsat8_Level1_Data_Format_Control_Book_LSDS-809
- Landsat 5-7: CNES internal format described in PSC-IF-411-0081-CNES_E1R4

MAJA is the processor used on [theia](http://www.theia-land.fr), to produce
Surface Reflance products.       

For more information about how to download and run MAJA check the [MAJA Software website]
(https://logiciels.cnes.fr/en/content/maja).

With MAJA, you will need to generate DEM tile to

This input will also used as input of LIS.

We'll process a tile near Mount Artos in Turkey

## Generate LIS JSON parameters using build_json.py

MAJA outputs consists in a directory with

In my case, I have a directory called:

```
S2A_OPER_SSC_L2VALD_38SLH____20180311.DBL.DIR

```
with the surface reflectances and could mask provided as GeoTiff.

And the DTM generates prepare_mnt tool available [here](http://tully.ups-tlse.fr/olivier/prepare_mnt). 

We're going to use the utilities script build_json.py to configure LIS and generate the parameter files.

This script takes as input the directory which contains the surface reflectance 
images, the output directory where the JSON parameter will be stored.

Sensors, filenames, band numbers, cloud mask encoding are automatically automatically retrieved from 
the directory name and structures. 

In the case of MAJA native format, you can let and only provides:

- the input directory with MAJA products
- the output directory where the json will be saved
- the directory where the DTM is stored

In the case of the Mount Artos tile, the command is:

```
build_json.py -dem S2__TEST_AUX_REFDE2_T38SLH_0001.DBL.DIR/S2__TEST_AUX_REFDE2_T38SLH_0001_ALT_R2.TIF  S2A_OPER_SSC_L2VALD_38SLH____20180311.DBL.DIR/ output_lis/
```

Note that the generated JSON file will use default parameters of the LIS processor. You can overload all parameters with build_json.py utility.

Please find below the complete help page of the build_json.py (all LIS parameters can be

```
build_json.py --help
usage: build_json.py [-h] [-nodata NODATA] [-ram RAM] [-nb_threads NB_THREADS]
                     [-generate_vector GENERATE_VECTOR]
                     [-preprocessing PREPROCESSING] [-log LOG] [-multi MULTI]
                     [-target_resolution TARGET_RESOLUTION] [-dem DEM]
                     [-cloud_mask CLOUD_MASK] [-dz DZ]
                     [-ndsi_pass1 NDSI_PASS1] [-red_pass1 RED_PASS1]
                     [-ndsi_pass2 NDSI_PASS2] [-red_pass2 RED_PASS2]
                     [-fsnow_lim FSNOW_LIM] [-fsnow_total_lim FSNOW_TOTAL_LIM]
                     [-shadow_in_mask SHADOW_IN_MASK]
                     [-shadow_out_mask SHADOW_OUT_MASK]
                     [-all_cloud_mask ALL_CLOUD_MASK]
                     [-high_cloud_mask HIGH_CLOUD_MASK] [-rf RF]
                     [-red_darkcloud RED_DARKCLOUD]
                     [-red_backtocloud RED_BACKTOCLOUD]
                     [-strict_cloud_mask STRICT_CLOUD_MASK]
                     inputPath outputPath

This script is used to generate the snow detector configuration json file.
This configuration requires at least the input product path and the output
path in which will be generated snow product.

positional arguments:
  inputPath             input product path (supports S2/L8/Take5 products)
  outputPath            output folder for the json configuration file, and
                        also the configured output path for the snow product

optional arguments:
  -h, --help            show this help message and exit

general:
  general parameters

  -nodata NODATA
  -ram RAM
  -nb_threads NB_THREADS
  -generate_vector GENERATE_VECTOR
                        true/false
  -preprocessing PREPROCESSING
                        true/false
  -log LOG              true/false
  -multi MULTI
  -target_resolution TARGET_RESOLUTION

inputs:
  input files

  -dem DEM              dem file path, to use for processing the input product
  -cloud_mask CLOUD_MASK
                        cloud mask file path

snow:
  snow parameters

  -dz DZ
  -ndsi_pass1 NDSI_PASS1
  -red_pass1 RED_PASS1
  -ndsi_pass2 NDSI_PASS2
  -red_pass2 RED_PASS2
  -fsnow_lim FSNOW_LIM
  -fsnow_total_lim FSNOW_TOTAL_LIM

cloud:
  cloud parameters

  -shadow_in_mask SHADOW_IN_MASK
  -shadow_out_mask SHADOW_OUT_MASK
  -all_cloud_mask ALL_CLOUD_MASK
  -high_cloud_mask HIGH_CLOUD_MASK
  -rf RF
  -red_darkcloud RED_DARKCLOUD
  -red_backtocloud RED_BACKTOCLOUD
  -strict_cloud_mask STRICT_CLOUD_MASK
                        true/false
```
## Run LIS
