
# How to generate configuration file for snow annual map computation on CNES HPC

This tutorial aims at describing and explaining the usage of the python script [prepare_data_for_snow_annual_map.py](https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow/blob/develop/hpc/prepare_data_for_snow_annual_map.py).

**WARNING: The following tutorial applies to LIS version 1.5 and only on CNES HPC.
However, it could be an example for generating custom preparation script outside of the CNES HPC**

## Prerequisites

The script prepare_data_for_snow_annual_map.py can only be launch on CNES HPC and with specific modules:
- Python in version 3.5.2
- Amalthee in version 0.2

On CNES HPC:
```
module load python/3.5.2
module load amalthee
```

The script prepare_data_for_snow_annual_map.py must be located along the following scripts, in order to launch correctly the sub-tasks:
- [run_lis_from_filelist.sh](https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow/blob/develop/hpc/run_lis_from_filelist.sh), it is a PBS script dedicated to the production of the snow products
- [run_snow_annual_map.sh](https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow/blob/develop/hpc/run_snow_annual_map.sh), it is a PBS script dedicated to the production of the snow annual maps

Note: It is possible to change the generation parameters of the intermediate snow products by editing the script run_lis_from_filelist.sh (cf. [build_json.py](https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow/blob/develop/app/build_json.py) parameters).
```
build_json.py -ram 2048 -dem $inputdem $zip_input_product $pout
```

## Configuration parameters

The scripts prepare_data_for_snow_annual_map.py does not take additional argument in itself. To edit the configuration, 
the script must be modified manually with any text editor. The section of the script to modify is reported below.

```
def main():
    params = {"tile_id":"T32TPS",
              "date_start":"01/09/2017",
              "date_stop":"31/08/2018",
              "date_margin":15,
              "mode":"DEBUG",
              "input_products_list":[],
              # path_tmp is an actual parameter but must only be uncomment with a correct path
              # else the processing use $TMPDIR by default
              #"path_tmp":"",
              "path_out":"/work/OT/siaa/Theia/Neige/SNOW_ANNUAL_MAP_LIS_1.5/L8_only",
              "ram":8192,
              "nbThreads":6,
              "use_densification":False,
              "log":True,
              "densification_products_list":[],
              # the following parameters are only use in this script, and doesn't affect snow_annual_map processing
              "snow_products_dir":"/work/OT/siaa/Theia/Neige/PRODUITS_NEIGE_LIS_develop_1.5",
              "data_availability_check":False}
```

These parameters are described in [snow_annual_map_schema.json](https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow/blob/develop/doc/snow_annual_map_schema.json)
and correspond to the parameters of the json file to provide to the application run_snow_annual_map.py.

However, the two last parameters are specific to prepare_data_for_snow_annual_map.py:
- "snow_products_dir", must be filled with the storage path chosen for all the snow products.
- "data_availability_check", must remains at "false" and is only modified by the script itself if all the data required for the snow annual map processing are available.

The only external configuration parameters is the following file:
- [selectNeigeSyntheseMultitemp.csv](https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow/blob/develop/hpc/selectNeigeSyntheseMultitemp.csv), it is the list of tiles (ex: "T31TCH") for which we want to generate the snow annual map.

## Execution

The script can now simply be launched by the following command:

```
python prepare_data_for_snow_annual_map.py
```

The generated log allows to monitor the status of the data requires before snow annual map processing.
In the case where all the required snow products are not already available in the **"snow_products_dir"** (which is more than likely!), the script will call two different types of asynchronous sub-processes:

 - the first one is a request for the generation of the missing snow products under **"snow_products_dir"**, when the L2A products are available.
 - the second one is triggered when some L2A products are not available, the sub-process in then in charge for the downloading of the products in to the datalake (see Amalthee documentation for command amalthee_theia.fill_datalake())

Because these sub-processes are asynchronous, it is required to run the prepare_data_for_snow_annual_map.py multiple time.
For example, if no data is available and that it is the first time you run the script, it would require to run it 3 times:
 - the first time to fill the datalake with the requested L2A products.
 - the second time to generate all the snow products corresponding to these L2A products
 - and finally to check that all the requested data is now available and to trigger the actual computation of the snow annual map.

Between each run it is adviced to monitor off-line the status of the different sub-processes, instead of running the script more than necessary.

## Results
