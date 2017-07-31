# Change Log
All notable changes to LIS will be documented in this file.

## [Unreleased]

### Added
- Use gdal_trace_outline from the gina-alaska package instead of gdal_polygonize if available

### Changed
- Move OTB minimum 6.0.0 which include a fix to handle properly 1 byte TIFF image
- New QGIS style files for raster and vector LIS product
- Use OTB Application Python API instead of call to subprocess
- Use Python Logging module for python scripts instead of using print

## [1.2] - 2017-06-04
- add json schema to ATBD to document all parameters
- Add version of lis in atbd
- Document how to build the documentation in doc/tex directory
- Compact histogram files and copy it in LIS_PRODUCTS
- Apply autopep8 to all Python scripts to imprve code quality
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
