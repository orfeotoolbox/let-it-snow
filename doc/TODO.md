# Snow Annual Maps: open points and perspectives

This files list the identifies open points, and also the actions in terms of data processing and production.

**WARNING: The following applies to LIS version 1.5**

## Densification using Landsat 8 products (old format)

The old format Landsat products are available through Theia. They were not used to densify the input snow products timeseries in the frame of the snow annual map generation (available under /work/OT/siaa/Theia/Neige/SNOW_ANNUAL_MAP_LIS_1.5). This can now be done by using the library [amalthee/0.2](https://gitlab.cnes.fr/datalake/amalthee.git). Among the parameters, it is possible to request products corresponding to a region of interest. This is the best way to retrive products corresponding to the S2 and L8 new format tiles (example: "T31TCH")

On CNES HPC:
```
module load amalthee/0.2
amalthee = Amalthee('oldlandsat')
amalthee.show_params("Landsat")
```

Once the old Landsat products are retrived and processed to obtain the snow products, the snow annual map could
be densified by simply adding them to the densification list. Please refer to [tutorials/prepare_snow_annual_map_data.md]((https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow/blob/develop/doc/tutorials/prepare_snow_annual_map_data.md))
for the usage of the script on CNES HPC.

## Modification of the [prepare_snow_annual_map_data.py](https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow/blob/develop/hpc/prepare_data_for_snow_annual_map.py)

This script must be modified to at least change the sub-processes that are currently asynchronous and that requires to run it multiple times.
