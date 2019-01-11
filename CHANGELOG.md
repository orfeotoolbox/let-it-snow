# Change Log
All notable changes to Let It Snow (LIS) will be documented in this file.

## [Unreleased]

### Added
- 

### Fixed
- 

## [1.5] - 2019-01-11

### Added
- The snow annual map module is now operational, the associated files are:
    - app/run_snow_annual_map.py, the main application
    - python/s2snow/snow_annual_map.py, the core of the annual map processing
    - python/s2snow/snow_annual_map_evaluation.py, provide the possibility to compare with other snow products and modis snow annual map
    - python/s2snow/snow_product_parser.py, class to handle the supported type of snow products
    - doc/snow_annual_map_schema.json, parameters descriptions
    - hpc/prepare_data_for_snow_annual_map.py, preprocessing script on CNES HPC, 
    - doc/tutorials/prepare_snow_annual_map_data.md, tutorial
- Provided new data pack for tests "Data-LIS-1.5"
- Add tests for snow annual map computation
- The version of the s2snow module is now stored in file python/s2snow/version.py
- Add support and tests for zipped products in build_json.py and run_snow_detector.py,
- Add a mode to build_json.py script to configure and run LIS on Level 2A MAJA native products
- Add a tutorial to describe how to run LIS on MAJA native products
- Add a mode to build_json.py script to configure and run LIS on SEN2COR Level 2A products
- Add a tutorial to describe how to run LIS on SEN2COR products
- Add a mode to build_json.py script to configure and run LIS on U.S. Landsat Analysis Ready Data (ARD) Level 2A products
- Add a tutorial to describe how to run LIS on Landsat ARD products	
- The expert mask now includes a 5th bit for the clouds that were present in the product/original cloud mask
- The expert mask now includes an optional 6th bit propagating the slope correction flag from the product mask when available
- The cold cloud removal (pass 1.5) now use an area threshold to process only significant snow areas within clouds and reduce time.
- Link ATBD and LIS Data for test validation to their Zenodo DOI in README.md

### Fixed
- Fix all python scripts headers to avoid to mix python versions
- Fix preprocessing json option which was broken which allows to resample input DTM
- Fix typos in README.md documentation
- Change nodata management (read -32768 from input and write 0 in the
    output) in DTM resampling to avoid error in snow line estimation
    on area without DTM information 

## [1.4] - 2018-02-14

### Added
- Experimental pass1_5 function implementing the removal of snow areas inside initial cloud mask (doughnuts)
- Experimental new application to run and evaluate an annual snow map computation from a timeserie of S2 and/or L8 snow products
- Added fclear_lim parameter minimum percentage of clear pixels in an elevation band
    (default value 0.1) used to compute the snow line.
- Added option to disable vector generation
- Added options to use and manage gdal_trace_outline instead of gdal_polygonize

### Changed
- Changed default value for parameter red_darkcloud to 300 to reduce cloud sensitivity
- Changed all_cloud_mask.tif, it now include the thin clouds (in accordance with ATBD)
- Fixed method compute_percent is fix when image is empty or filled with nodata
- Fixed zs condition to trigger properly pass2 (in accordance with ATBD)
- Changed zs computation in pass2 to considers the full image imprint (including nodata pixels)
- Changed cloud mask refinement is not apply during pass1 to improve snow line accuracy during pass2
- Updated build_json.py to handle boolean parameters
- Updated build_json.py to handle new lis input parameters

## [1.3.1] - 2017-11-23

### Fixed
- Fix the intermediate data format (used 1 bit instead of type uint8)

## [1.3] - 2017-11-02

### Added
- Use gdal_trace_outline from the gina-alaska package instead of gdal_polygonize if available

### Changed
- Move OTB minimum 6.0.0 which include a fix to handle properly 1 byte TIFF image
- Restore and document correct behaviour for LIS installation with install target(lib, bin,include, python) 
- New QGIS style files for raster and vector LIS product
- Use OTB Application Python API instead of call to subprocess
- Use Python Logging module for Python scripts instead of using print
- Changed compute_cloud_mask and compute_snow_mask by OTB applications
- Added a new app to generate the JSON configuration file (build_json.py)
- Changed the way the product is generated to avoid data duplication
- Change rasterize step to contour detection using 8 connectivity to generate the rgb composition
- Improved detection by adjusting default parameter red_pass2 from 0.120 to 0.40
- Improve code quality (pep8 and pylint)
- Improve installation instructions in the README.md
- Fix cpu usage to respect the "nb_threads" parameter set in the json file.
- The output product now use the input product directory name as PRODUCT_ID in the xml file.

## [1.2.1] - 2017-09-14
- Fix segfault in case number of histogram bins for the altitude channel is zero 

## [1.2] - 2017-06-04
- add json schema to ATBD to document all parameters
- Add version of lis in atbd
- Document how to build the documentation in doc/tex directory
- Compact histogram files and copy it in LIS_PRODUCTS
- Apply autopep8 to all Python scripts to improve code quality
- Add a changelog

## [1.1.1] - 2016-11-28
- minor update in build scripts
- change ctest launcher location

## [1.1.0] - 2016-11-28
- Change license from GPL to A-GPL
- Improvments in cmake configuration
- launch tests in separate directories

## [1.0.0] - 2016-07-06
- First released version of LIS with support with last MUSCATE format
- Support for image splitted in multiple files
- Use high clouds mask in cloud refine
- Prototype for multi-T synthesis
